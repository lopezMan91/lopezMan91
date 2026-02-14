from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from .transactions import PolicyLine, Transaction, TransactionManager


@dataclass(frozen=True)
class BusinessEvent:
    event_id: str
    event_type: str
    source_ref: str
    company: str
    currency: str
    occurred_at: str
    payload: dict[str, Any]


@dataclass
class Ledger:
    code: str
    name: str
    principle: str
    dominant_standard: str = "NIF"


@dataclass
class PostingRun:
    run_id: str
    rule_version: str
    executed_at: str
    event_id: str
    logs: list[str] = field(default_factory=list)


@dataclass
class JournalLine:
    account: str
    debit: Decimal
    credit: Decimal
    description: str


@dataclass
class JournalEntry:
    entry_id: str
    company: str
    ledger_code: str
    event_id: str
    policy_id: str
    lines: list[JournalLine]
    integrity_hash: str = ""


@dataclass
class AccountingPolicy:
    version: str
    event_type: str
    ledger_code: str
    line_rules: list[dict[str, str]]


@dataclass
class AccrualTemplate:
    template_id: str
    description: str
    debit_account: str
    credit_account: str
    amount_expr: str
    ledger_code: str = "LOCAL"


class AccountingEngine:
    def __init__(self, manager: TransactionManager):
        self.manager = manager
        self.ledgers: dict[str, Ledger] = {
            "LOCAL": Ledger("LOCAL", "Local NIF/SAT", "NIF/SAT"),
            "IFRS": Ledger("IFRS", "IFRS", "IFRS"),
            "CONSOL": Ledger("CONSOL", "Consolidation", "IFRS"),
            "ELIM": Ledger("ELIM", "Eliminations", "IFRS"),
        }
        self.entries: list[JournalEntry] = []

    def set_ledger_dominant_standard(self, ledger_code: str, standard: str):
        """Configure dominant accounting standard by ledger (NIF/IFRS/USGAAP)."""
        ledger = self.ledgers.get(ledger_code)
        if not ledger:
            raise ValueError(f"Ledger inexistente: {ledger_code}")
        ledger.dominant_standard = standard

    def post_event(self, event: BusinessEvent, policies: list[AccountingPolicy]) -> PostingRun:
        run = PostingRun(
            run_id=f"RUN-{len(self.entries) + 1:05d}",
            rule_version=",".join(sorted({p.version for p in policies})) or "N/A",
            executed_at=datetime.utcnow().isoformat(),
            event_id=event.event_id,
        )

        lines_to_post: list[PolicyLine] = []

        for policy in policies:
            if policy.event_type != event.event_type:
                continue
            if policy.ledger_code not in self.ledgers:
                run.logs.append(f"Ledger inexistente: {policy.ledger_code}")
                continue

            policy_id = f"{event.event_id}-{policy.ledger_code}"
            entry_lines: list[JournalLine] = []
            for idx, rule in enumerate(policy.line_rules, start=1):
                debit = _money(_eval_amount(rule.get("debit", "0"), event.payload))
                credit = _money(_eval_amount(rule.get("credit", "0"), event.payload))
                account = rule.get("account", "0000")
                desc = rule.get("description", event.event_type)
                entry_lines.append(JournalLine(account=account, debit=debit, credit=credit, description=desc))
                lines_to_post.append(PolicyLine(
                    policy_id=policy_id,
                    date=event.occurred_at,
                    description=f"{desc} L{idx} {policy.ledger_code}",
                    account=account,
                    debit=float(debit),
                    credit=float(credit),
                    category=f"ledger_{policy.ledger_code.lower()}",
                ))

            self.entries.append(JournalEntry(
                entry_id=f"JE-{len(self.entries) + 1:05d}",
                company=event.company,
                ledger_code=policy.ledger_code,
                event_id=event.event_id,
                policy_id=policy_id,
                lines=entry_lines,
                integrity_hash=_entry_integrity_hash(
                    f"JE-{len(self.entries) + 1:05d}",
                    event.company,
                    policy.ledger_code,
                    event.event_id,
                    entry_lines,
                ),
            ))
            run.logs.append(f"Generada póliza {policy_id} en {policy.ledger_code}")

        if lines_to_post:
            self.manager.post_policy_lines(lines_to_post)
        else:
            run.logs.append("No hubo reglas aplicables")
        return run

    def create_accrual_with_auto_reversal(
        self,
        event: BusinessEvent,
        template: AccrualTemplate,
        reversal_date: str,
    ) -> PostingRun:
        """Create accrual entry and automatic reversal (NIF A-2 devengación)."""
        amount = _money(_eval_amount(template.amount_expr, event.payload))
        if amount <= Decimal("0.00"):
            raise ValueError("Monto de provisión debe ser positivo")

        accrual_policy = AccountingPolicy(
            version="accrual-v1",
            event_type=event.event_type,
            ledger_code=template.ledger_code,
            line_rules=[
                {"account": template.debit_account, "debit": f"{amount}", "credit": "0", "description": template.description},
                {"account": template.credit_account, "debit": "0", "credit": f"{amount}", "description": f"{template.description} (provisión)"},
            ],
        )
        run = self.post_event(event, [accrual_policy])

        reversal_event = BusinessEvent(
            event_id=f"{event.event_id}-REV",
            event_type=event.event_type,
            source_ref=f"{event.source_ref}-REV",
            company=event.company,
            currency=event.currency,
            occurred_at=reversal_date,
            payload=event.payload,
        )
        reversal_policy = AccountingPolicy(
            version="accrual-v1-rev",
            event_type=reversal_event.event_type,
            ledger_code=template.ledger_code,
            line_rules=[
                {"account": template.credit_account, "debit": f"{amount}", "credit": "0", "description": f"Reversa {template.description}"},
                {"account": template.debit_account, "debit": "0", "credit": f"{amount}", "description": f"Reversa {template.description}"},
            ],
        )
        rev_run = self.post_event(reversal_event, [reversal_policy])
        run.logs.extend(rev_run.logs)
        return run


def _eval_amount(expr: str, payload: dict[str, Any]) -> Decimal:
    cleaned = expr.strip()
    if cleaned.startswith("payload."):
        return _money(payload.get(cleaned.split(".", 1)[1], 0) or 0)
    return _money(cleaned or 0)


def drilldown_for_ledger(transactions: list[Transaction], ledger_code: str) -> list[Transaction]:
    prefix = f"ledger_{ledger_code.lower()}"
    return [t for t in transactions if t.category.startswith(prefix)]


def _entry_integrity_hash(
    entry_id: str,
    company: str,
    ledger_code: str,
    event_id: str,
    lines: list[JournalLine],
) -> str:
    base = [entry_id, company, ledger_code, event_id]
    for line in lines:
        base.append(f"{line.account}|{line.debit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}|{line.credit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}|{line.description}")
    return sha256("||".join(base).encode("utf-8")).hexdigest()


def verify_entry_integrity(entry: JournalEntry) -> bool:
    expected = _entry_integrity_hash(
        entry.entry_id,
        entry.company,
        entry.ledger_code,
        entry.event_id,
        entry.lines,
    )
    return expected == entry.integrity_hash


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

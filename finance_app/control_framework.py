from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Control:
    code: str
    process: str
    control_type: str  # preventive/detective
    frequency: str
    owner: str
    severity: str


@dataclass
class SODRule:
    role_a: str
    role_b: str
    description: str


@dataclass
class ControlLibrary:
    controls: list[Control] = field(default_factory=list)
    sod_rules: list[SODRule] = field(default_factory=list)

    def add_control(self, control: Control):
        self.controls.append(control)

    def add_sod_rule(self, rule: SODRule):
        self.sod_rules.append(rule)

    def evaluate_user_roles(self, roles: list[str]) -> list[str]:
        role_set = set(roles)
        issues: list[str] = []
        for rule in self.sod_rules:
            if rule.role_a in role_set and rule.role_b in role_set:
                issues.append(f"Conflicto SoD: {rule.role_a} + {rule.role_b} ({rule.description})")
        return issues


def default_control_library() -> ControlLibrary:
    lib = ControlLibrary()
    lib.add_control(Control("P2P-001", "P2P", "preventive", "daily", "AP Lead", "high"))
    lib.add_control(Control("R2R-010", "R2R", "detective", "monthly", "Controller", "high"))
    lib.add_sod_rule(SODRule("vendor_create", "payment_approve", "Alta de proveedor vs aprobación de pagos"))
    lib.add_sod_rule(SODRule("journal_post", "period_reopen", "Posteo de póliza vs reapertura de periodos"))
    return lib

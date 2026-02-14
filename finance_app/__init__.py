"""Modulo principal de la aplicacion Finance Manager."""

from .transactions import PolicyLine, PolicyPostingSummary, Transaction, TransactionManager
from .budget import Budget
from .import_export import ImportExport
from .analysis import Analysis
from .goals import Goal, GoalManager
from .notifications import notify
from .user import User, UserManager
from .financial_statements import FinancialStatements
from .policy_import import PolicyPostResult, import_and_post_policies
from .accounting_core import AccountingEngine, AccountingPolicy, BusinessEvent, Ledger, PostingRun, drilldown_for_ledger
from .fiscal_compliance import FiscalDocument, FiscalVault
from .report_builder import FinancialStatementBuilder, ReportingTemplate, default_templates
from .control_framework import ControlLibrary, Control, SODRule, default_control_library
from .reconciliation import ReconciliationItem, ReconciliationWorkflow
from .reconciliation import BankStatementLine, LedgerLine, ReconciliationMatch, suggest_fuzzy_matches
from .journal_importer import JournalImportStaging, JournalTemplateImporter
from .smart_classification import ClassificationSuggestion, suggest_account_and_cost_center
from .tax_engine_mx import (
    FiscalLine,
    ISRReconciliationResult,
    IVASummaryResult,
    TaxEngineMX,
    TaxEvidencePack,
    TaxLineAttributes,
    TemporaryDifference,
)
from .intangibles_engine import (
    IntangibleAsset,
    IntangibleEvidence,
    IntangiblesEngine,
    IntangibleRollforward,
    IntangibleTransaction,
)
from .revenue_ifrs15 import (
    ContractRollforward,
    PerformanceObligation,
    RevenueContract,
    RevenueEngineIFRS15,
    RevenueRecognitionLine,
)
from .lease_engine import (
    LeaseAmortizationLine,
    LeaseContract,
    LeaseDiscountRate,
    LeaseEngine,
    LeaseMeasurementSnapshot,
    LeaseModification,
    LeasePaymentSchedule,
    LeasePostingBatch,
    remeasure_contract,
)


def get_exchange_rate() -> float:
    """Lazy wrapper to avoid loading external dependencies at import time."""
    from .api import get_exchange_rate as _get_exchange_rate

    return _get_exchange_rate()


__all__ = [
    "PolicyLine",
    "PolicyPostingSummary",
    "Transaction",
    "TransactionManager",
    "Budget",
    "ImportExport",
    "Analysis",
    "Goal",
    "GoalManager",
    "notify",
    "User",
    "UserManager",
    "FinancialStatements",
    "PolicyPostResult",
    "AccountingEngine",
    "AccountingPolicy",
    "BusinessEvent",
    "Ledger",
    "PostingRun",
    "drilldown_for_ledger",
    "FiscalDocument",
    "FiscalVault",
    "FinancialStatementBuilder",
    "ReportingTemplate",
    "default_templates",
    "ControlLibrary",
    "Control",
    "SODRule",
    "default_control_library",
    "ReconciliationItem",
    "ReconciliationWorkflow",
    "BankStatementLine",
    "LedgerLine",
    "ReconciliationMatch",
    "suggest_fuzzy_matches",
    "ClassificationSuggestion",
    "suggest_account_and_cost_center",
    "JournalImportStaging",
    "JournalTemplateImporter",
    "LeaseAmortizationLine",
    "LeaseContract",
    "LeaseDiscountRate",
    "LeaseEngine",
    "LeaseMeasurementSnapshot",
    "LeaseModification",
    "LeasePaymentSchedule",
    "LeasePostingBatch",
    "remeasure_contract",
    "FiscalLine",
    "TaxLineAttributes",
    "TaxEvidencePack",
    "TemporaryDifference",
    "TaxEngineMX",
    "IVASummaryResult",
    "ISRReconciliationResult",
    "IntangibleAsset",
    "IntangibleEvidence",
    "IntangibleTransaction",
    "IntangibleRollforward",
    "IntangiblesEngine",
    "PerformanceObligation",
    "RevenueContract",
    "RevenueRecognitionLine",
    "ContractRollforward",
    "RevenueEngineIFRS15",
    "import_and_post_policies",
    "get_exchange_rate",
]

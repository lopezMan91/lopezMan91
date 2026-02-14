from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256


@dataclass
class FiscalDocument:
    uuid: str
    rfc_emisor: str
    rfc_receptor: str
    total: float
    xml_content: str
    sat_status: str = "vigente"

    @property
    def xml_hash(self) -> str:
        return sha256(self.xml_content.encode("utf-8")).hexdigest()


@dataclass
class FiscalLink:
    policy_id: str
    uuid: str
    event_id: str


@dataclass
class FiscalVault:
    documents: dict[str, FiscalDocument] = field(default_factory=dict)
    links: list[FiscalLink] = field(default_factory=list)

    def ingest_document(self, document: FiscalDocument):
        self.documents[document.uuid] = document

    def link_policy_uuid(self, policy_id: str, uuid: str, event_id: str):
        if uuid not in self.documents:
            raise ValueError(f"UUID no encontrado: {uuid}")
        self.links.append(FiscalLink(policy_id=policy_id, uuid=uuid, event_id=event_id))

    def verify_closing_gates(self) -> list[str]:
        issues: list[str] = []
        linked_policy_ids = {ln.policy_id for ln in self.links}

        for link in self.links:
            document = self.documents.get(link.uuid)
            if not document:
                issues.append(f"Póliza {link.policy_id} sin CFDI en vault")
                continue
            if document.sat_status.lower() != "vigente":
                issues.append(f"CFDI {link.uuid} en estatus {document.sat_status}")

        if not linked_policy_ids:
            issues.append("No hay pólizas ligadas a UUID")

        return issues

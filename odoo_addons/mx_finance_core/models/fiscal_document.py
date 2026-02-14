from odoo import api, fields, models


class MxFiscalDocument(models.Model):
    _name = "mx.fiscal.document"
    _description = "CFDI Fiscal Vault Document"

    name = fields.Char(required=True)
    uuid = fields.Char(required=True, index=True)
    rfc_emisor = fields.Char(required=True)
    rfc_receptor = fields.Char(required=True)
    total = fields.Float(required=True)
    xml_file = fields.Binary(required=True)
    xml_filename = fields.Char()
    xml_hash = fields.Char(readonly=True)
    sat_status = fields.Selection([
        ("vigente", "Vigente"),
        ("cancelado", "Cancelado"),
        ("no_encontrado", "No encontrado"),
    ], default="vigente", required=True)
    lco_status = fields.Selection([
        ("listed", "Listed"),
        ("not_listed", "Not Listed"),
        ("unknown", "Unknown"),
    ], default="unknown", required=True)
    efos_status = fields.Selection([
        ("clean", "Clean"),
        ("listed", "Listed"),
        ("unknown", "Unknown"),
    ], default="unknown", required=True)
    compliance_blocked = fields.Boolean(compute="_compute_compliance_blocked", store=True)
    event_id = fields.Many2one("mx.accounting.event")
    move_id = fields.Many2one("account.move")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.xml_hash = f"{rec.uuid}:{rec.total}:{rec.rfc_emisor}"
        return records

    @api.depends("sat_status", "lco_status", "efos_status")
    def _compute_compliance_blocked(self):
        for rec in self:
            rec.compliance_blocked = (
                rec.sat_status != "vigente"
                or rec.lco_status != "listed"
                or rec.efos_status == "listed"
            )

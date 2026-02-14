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
    event_id = fields.Many2one("mx.accounting.event")
    move_id = fields.Many2one("account.move")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.xml_hash = f"{rec.uuid}:{rec.total}:{rec.rfc_emisor}"
        return records

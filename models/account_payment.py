from odoo import _, api, fields, models
from lxml import etree

class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.onchange("journal_id")
    def domain_journal_id(self):
        journal_ids = self._context.get("journal_ids")
        if journal_ids and len(journal_ids) > 0:
            domain = {"journal_id": [("type", "in", ["bank","cash"]), ("id", "in", journal_ids)]}
            return {"domain": domain}
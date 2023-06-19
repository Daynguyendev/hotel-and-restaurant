from odoo import _, api, fields, models

class AccountJournal(models.Model):
    _inherit = "account.journal"

    hotel_restaurant_branch_id = fields.Many2one("sea.hotel.restaurant.branch", string="Hotel&Res Branch")
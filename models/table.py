from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Table(models.Model):
    _name = "sea.restaurant.table"
    _description = "Table of restaurant"

    name = fields.Char("Table Name", required=True, index=True)
    capacity = fields.Integer("Capacity")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    hotel_restaurant_area_id = fields.Many2one(
        "sea.hotel.restaurant.area", string="Table Area", help="At which area the table is located.",
        domain="[('company_id', '=', company_id)]",)
    # không domain theo pos
    # domain="[('pos_hotel_restaurant_id', '=', pos_hotel_restaurant_id)]",)
    status = fields.Selection(
        [("available", "Available"), ("occupied", "Occupied"), ("maintained", "Maintained")],
        "Status",
        default="available",
    )
    pos_hotel_restaurant_id = fields.Many2one('sea.pos.hotel.restaurant', string='Point of Sale', require=True,
                                              domain="[('company_id', '=', company_id)]")

    #  domain=lambda self: self.domain_pos_by_user()
    #  Cái này của pos_hotel_restaurant_id do em domain lại theo brand nên tạm để đây
    # bàn chỉ thuộc pos không thuộc branch
    # branch_id = fields.Many2one('sea.hotel.restaurant.branch', string='Branch',
    # domain="[('company_id', '=', company_id)]")
    # @api.onchange('branch')
    # def _onchange_pos_hotel_restaurant(self):
    #     res = {'domain': {
    #         'pos_hotel_restaurant_id': [('hotel_restaurant_branch_id', '=', self.branch_id.id)]}}
    #     return res
    # @api.model
    # def domain_pos_by_user(self):
    #     user_branch = []
    #     branches = self.env["sea.hotel.restaurant.branch"].sudo().search([])
    #     for branch in branches:
    #         if self.env.user.partner_id.id in [user.partner_id.id for user in branch.user_ids]:
    #             user_branch.append(branch.id)
    #     domain = [
    #         ("company_id", "=", self.env.user.company_id.id),
    #         ("hotel_restaurant_branch_id", "in", user_branch),
    #         ("pos_type", "=", "restaurant")
    #     ]
    #     return domain

    @api.multi
    def write(self, vals):
        # if "available" in vals:
        #     if vals["available"] is True:
        #         vals["status"] = "available"
        #     elif vals["available"] is False:
        #         vals["status"] = "occupied"
        return super(Table, self).write(vals)

    @api.constrains("capacity")
    def check_capacity(self):
        for room in self:
            if room.capacity <= 0:
                raise ValidationError(_("Room capacity must be more than 0"))

    # @api.onchange("available")
    # def table_status_change(self):
    #     """
    #     Based on isroom, status will be updated.
    #     ----------------------------------------
    #     @param self: object pointer
    #     """
    #     if self.available is False:
    #         self.status = "occupied"
    #     if self.available is True:
    #         self.status = "available"

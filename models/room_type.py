from odoo import _, api, fields, models


class RoomType(models.Model):
    _name = "sea.hotel.room.type"
    _description = "Hotel Room Type"

    name = fields.Char(string="Room Type", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    parent_type_id = fields.Many2one("sea.hotel.room.type", "Parent type", domain="[('company_id', '=', company_id)]")
    # pos_hotel_restaurant_id = fields.Many2one('sea.pos.hotel.restaurant', string='Point of Sale', require=True)
    # domain=lambda self: self.domain_pos_by_user()
    # Cái này của pos_hotel_restaurant_id do em domain lại theo brand nên tạm để đây
    # branch_id = fields.Many2one('sea.hotel.restaurant.branch', string='Branch')
    # @api.onchange('branch')
    # def _onchange_pos_hotel_restaurant(self):
    #     res = {'domain': {
    #         'pos_hotel_restaurant_id': [('hotel_restaurant_branch_id', '=', self.branch_id.id)]}}
    #     return res

    # @api.onchange('parent_type_id')
    # def _onchange_parent_type(self):
    #     res = {'domain': {
    #         'parent_type_id': [('branch_id', '=', self.branch_id.id)]}}
    #     print('test res',res)
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
    #         ("pos_type", "=", "hotel"),
    #     ]
    #     return domain

    room_ids = fields.One2many('sea.hotel.room', 'room_type_id', string='Rooms')

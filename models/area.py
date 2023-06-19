from odoo import fields, models


class Area(models.Model):
    _name = "sea.hotel.restaurant.area"
    _description = "Hotel & Restaurant Area"

    name = fields.Char("Area Name", required=True, index=True)
    # area_type = fields.Selection(
    #     [("hotel", "Hotel Area"), ("restaurant", "Restaurant Area")],
    #     default="hotel", string="Area Type", require=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    # Khu vực không thuộc branch và pos mà thuộc company_id
    # pos_hotel_restaurant_id = fields.Many2one('sea.pos.hotel.restaurant', string='Point of Sale', require=True)
    #  domain=lambda self: self.domain_pos_by_user()
    #  Cái này của pos_hotel_restaurant_id do em domain lại theo brand nên tạm để đây
    # branch_id = fields.Many2one('sea.hotel.restaurant.branch', string='Branch')
    # @api.onchange('branch')
    # def _onchange_pos_hotel_restaurant(self):
    #         res = {}
    #         res['domain'] = {
    #             'pos_hotel_restaurant_id': [('hotel_restaurant_branch_id', '=', self.branch_id.id)]}
    #         return res
    # @api.model
    # def domain_pos_by_user(self):
    #     user_branch = []
    #     branches = self.env["sea.hotel.restaurant.branch"].sudo().search([])
    #     for branch in branches:
    #         if self.env.user.partner_id.id in [user.partner_id.id for user in branch.user_ids]:
    #             user_branch.append(branch.id)
    #     domain = [
    #         ("company_id", "=", self.env.user.company_id.id),
    #         ("hotel_restaurant_branch_id", "in", user_branch)
    #     ]
    #     return domain
    def compute_pos(self):
        for rec in self:
            pos = []
            if rec.room_ids:
                for i in rec.room_ids:
                    if i.pos_hotel_restaurant_id.id not in pos:
                        pos.append(i.pos_hotel_restaurant_id.id)
            if rec.table_ids:
                for i in rec.table_ids:
                    if i.pos_hotel_restaurant_id.id not in pos:
                        pos.append(i.pos_hotel_restaurant_id.id)
            if pos is not None:
                rec.pos_hotel_restaurant_id = [(4, record_id, False) for record_id in pos]
            else:
                rec.pos_hotel_restaurant_id = [(6, 0, [])]

    pos_hotel_restaurant_id = fields.Many2many('sea.pos.hotel.restaurant', string='Point of Sale',
                                               compute='compute_pos')
    room_ids = fields.One2many('sea.hotel.room', 'hotel_restaurant_area_id', string='Rooms')
    table_ids = fields.One2many('sea.restaurant.table', 'hotel_restaurant_area_id', string='Tables')

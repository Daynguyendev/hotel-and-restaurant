from odoo import _, api, fields, models


class RoomType(models.Model):
    _name = "sea.hotel.room.type"
    _description = "Hotel Room Type"

    name = fields.Char(string="Room Type", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    parent_type_id = fields.Many2one("sea.hotel.room.type", "Parent type", domain="[('company_id', '=', company_id)]")
    # pos_hotel_restaurant_id = fields.Many2one('sea.pos.hotel.restaurant', string='Point of Sale', require=True)
    room_ids = fields.One2many('sea.hotel.room', 'room_type_id', string='Rooms')

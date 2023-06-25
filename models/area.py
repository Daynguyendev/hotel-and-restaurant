from odoo import fields, models


class Area(models.Model):
    _name = "sea.hotel.restaurant.area"
    _description = "Hotel & Restaurant Area"

    name = fields.Char("Area Name", required=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

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

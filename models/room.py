from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Room(models.Model):
    _name = "sea.hotel.room"
    _description = "Hotel Room"

    name = fields.Char(string="Room Name", require=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    capacity = fields.Integer(string="Capacity", required=True)
    status = fields.Selection(
        [("available", "Available"), ("occupied", "Occupied"), ("maintained", "Maintained"), ("cleaned", "Cleaned")],
        default="available",
        string="Status",
    )
    pos_hotel_restaurant_id = fields.Many2one('sea.pos.hotel.restaurant', string='Point of Sale', require=True)
    hotel_restaurant_area_id = fields.Many2one(
        "sea.hotel.restaurant.area", string="Area", help="At which area the room is located.",
        domain="[('company_id', '=', company_id)]"
    )
    room_type_id = fields.Many2one(
        "sea.hotel.room.type", String="Room Type",
        domain="[('company_id', '=', company_id)]"
    )
    product_ids = fields.Many2many("product.product", "sea_room_product_rel", "room_id", "product_id", string="Room Available")
    product_default = fields.Many2one("product.product",required=True, string="Room Default")
    default_amenities = fields.One2many(
        "sea.hotel.room.line", "product_sea_hotel_room", string="Default amenities")
    # branch = fields.Many2one('sea.hotel.restaurant.branch', string='Branch')

    @api.multi
    def write(self, vals):
        # if "available" in vals:
        #     if vals["available"] is True:
        #         vals["status"] = "available"
        #     elif vals["available"] is False:
        #         vals["status"] = "occupied"
        return super(Room, self).write(vals)

    @api.constrains("capacity")
    def check_capacity(self):
        for room in self:
            if room.capacity <= 0:
                raise ValidationError(_("Room capacity must be more than 0"))

class HotelRoomLine(models.Model):
    _name = "sea.hotel.room.line"

    product_id = fields.Many2one("product.product")
    product_sea_hotel_room = fields.Many2one("sea.hotel.room")
    quantity = fields.Float(string="Quantity")

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
        # domain = "[('pos_hotel_restaurant_id', '=', pos_hotel_restaurant_id)]"
    )
    room_type_id = fields.Many2one(
        "sea.hotel.room.type", String="Room Type",
        domain="[('company_id', '=', company_id)]"
        # domain="[('pos_hotel_restaurant_id', '=', pos_hotel_restaurant_id)]"
    )
    product_ids = fields.Many2many("product.product", "sea_room_product_rel", "room_id", "product_id", string="Room Available")
    product_default = fields.Many2one("product.product",required=True, string="Room Default")
    default_amenities = fields.One2many(
        "sea.hotel.room.line", "product_sea_hotel_room", string="Default amenities")
    # branch = fields.Many2one('sea.hotel.restaurant.branch', string='Branch')
    # @api.onchange('branch')
    # def _onchange_pos_hotel_restaurant(self):
    #         res = {}
    #         res['domain'] = {
    #             'pos_hotel_restaurant_id': [('hotel_restaurant_branch_id', '=', self.branch.id)]}
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
    #         ("hotel_restaurant_branch_id", "in", user_branch),
    #         ("pos_type", "=", "hotel"),
    #     ]
    #     return domain

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

    # @api.onchange("available")
    # def room_status_change(self):
    #     """
    #     Based on isroom, status will be updated.
    #     ----------------------------------------
    #     @param self: object pointer
    #     """
    #     if self.available is False:
    #         self.status = "occupied"
    #     if self.available is True:
    #         self.status = "available"


class HotelRoomLine(models.Model):
    _name = "sea.hotel.room.line"

    product_id = fields.Many2one("product.product")
    product_sea_hotel_room = fields.Many2one("sea.hotel.room")
    quantity = fields.Float(string="Quantity")

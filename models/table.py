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
    status = fields.Selection(
        [("available", "Available"), ("occupied", "Occupied"), ("maintained", "Maintained")],
        "Status",
        default="available",
    )
    pos_hotel_restaurant_id = fields.Many2one('sea.pos.hotel.restaurant', string='Point of Sale', require=True,
                                              domain="[('company_id', '=', company_id)]")

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

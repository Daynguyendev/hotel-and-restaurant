from odoo import _, api, fields, models


class POSHotelRestaurant(models.Model):
    _name = "sea.pos.hotel.restaurant"
    _description = "POS of hotel and restaurant"

    def _default_pricelist(self):
        return self.env['product.pricelist'].search([('company_id', 'in', (False, self.env.user.company_id.id)),
                                                     ('currency_id', '=', self.env.user.company_id.currency_id.id)],
                                                    limit=1)

    name = fields.Char(string="Point of Sale Name", index=True, required=True,
                       help="An internal identification of the point of sale.")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    hotel_restaurant_branch_id = fields.Many2one("sea.hotel.restaurant.branch", string="Branch", require=True,
                                                 domain="[('company_id', '=', company_id)]")
    pos_type = fields.Selection([
        ("restaurant", "Restaurant"),
        ("hotel", "Hotel")
    ], string="POS's Type", default="restaurant", require=True)

    '''POS users'''
    user_ids = fields.Many2many('res.users', string='POS User')

    '''POS Display '''
    limit_categories = fields.Boolean("Restrict Available Product Categories")
    iface_available_categ_ids = fields.Many2many('pos.category', string='Available PoS Product Categories',
                                                 help='The point of sale will only display products \n'
                                                      'which are within one of the selected category trees. \n'
                                                      'If no category is specified, all available'
                                                      'products will be shown',
                                                 domain=lambda self: [("company_id", "=", self.env.user.company_id.id)])
    qty_available_product = fields.Boolean("Show quanity available product", default=False)

    '''Pricing'''
    iface_tax_included = fields.Selection([('subtotal', 'Tax-Excluded Price'), ('total', 'Tax-Included Price')],
                                          string="Tax Display", default='subtotal', required=True)
    available_pricelist_ids = fields.Many2many('product.pricelist', string='Available Pricelists',
                                               default=_default_pricelist)

    '''Inventory'''
    picking_type_id = fields.Many2one("stock.picking.type", string="Operation Type",
                                      domain="[('warehouse_id', '=', False)]")
    pos_location_id = fields.Many2one("stock.location", string="Default POS location",
                                      domain=lambda self: [("company_id", "=", self.env.user.company_id.id),
                                                           ("usage", "=", "internal")])
    default_route_id = fields.Many2one("stock.location.route", string="Default route")
    custom_routes_id = fields.Many2many('stock.location.route', string='Custom routes')
    allow_out_of_stock = fields.Boolean("Allow out of stock", default=True)

    '''Accounting'''
    payment_journal_ids = fields.Many2many('account.journal', string='Payment journals')
    invoice_journal_id = fields.Many2one("account.journal", string="Accounting invoice journal")

    '''Order and Booking'''
    customer_default_id = fields.Many2one("res.partner", string='Customer default',
                                          domain="[('company_id', '=', company_id)]")
    digit_of_discount = fields.Integer(string="Digits of Discount")

    @api.onchange('hotel_restaurant_branch_id')
    def _onchange_picking_type(self):
        if self.hotel_restaurant_branch_id.warehouse_id:
            res = {'domain': {
                'picking_type_id': [('warehouse_id', '=', self.hotel_restaurant_branch_id.warehouse_id.id)]}}
            return res

    @api.multi
    def action_open_hotel_order_view(self):
        hotel_order_tree_view = self.env.ref('sea_hotel_restaurant.hotel_order_tree_view')
        hotel_order_form_view = self.env.ref('sea_hotel_restaurant.hotel_order_form_view')
        return {
            'name': _(self.name),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'views': [(hotel_order_tree_view.id, 'tree'), (hotel_order_form_view.id, 'form')],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('order_type', '=', 'hotel_order'), ('pos_hotel_restaurant_id', '=', self.id)],
            'context': {'search_default_order_sale': 1, 'default_order_type': 'hotel_order',
                        'default_pos_hotel_restaurant_id': self.id,
                        'default_warehouse_id': self.hotel_restaurant_branch_id.warehouse_id.id,
                        'default_partner_id': self.customer_default_id.id},
            'target': 'current',
        }

    @api.multi
    def action_open_restaurant_order_view(self):
        restaurant_order_tree_view = self.env.ref('sea_hotel_restaurant.restaurant_order_tree_view')
        restaurant_order_form_view = self.env.ref('sea_hotel_restaurant.restaurant_order_form_view')
        return {
            'name': _(self.name),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'views': [(restaurant_order_tree_view.id, 'tree'), (restaurant_order_form_view.id, 'form')],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('order_type', '=', 'restaurant_order'), ('pos_hotel_restaurant_id', '=', self.id)],
            'context': {'search_default_order_sale': 1, 'default_order_type': 'restaurant_order',
                        'default_pos_hotel_restaurant_id': self.id,
                        'default_warehouse_id': self.hotel_restaurant_branch_id.warehouse_id.id,
                        'default_partner_id': self.customer_default_id.id},
            'target': 'current',
        }

    # @api.multi
    # def action_open_table_order_view(self):
    #     return {
    #         'name': 'Table Orders',
    #         'type': 'ir.actions.client',
    #         'tag': 'table_create_order_view_base',
    #         'target': 'main',
    #         'context': {"pos_id": self.id}
    #     }
    #
    # @api.multi
    # def action_open_restaurant_kitchen_view(self):
    #     return {
    #         'name': 'Kitchen',
    #         'type': 'ir.actions.client',
    #         'tag': 'kitchen_view_base',
    #         'target': 'main',
    #         'context': {"pos_id": self.id}
    #     }

from odoo import _, api, models, fields


class HotelRestaurantBranch(models.Model):
    _name = "sea.hotel.restaurant.branch"
    _description = "Hotel and Restaurant's Branch"

    def _default_pricelist(self):
        return self.env['product.pricelist'].search([('company_id', 'in', (False, self.env.user.company_id.id)),
                                                     ('currency_id', '=', self.env.user.company_id.currency_id.id)],
                                                    limit=1)

    name = fields.Char("Branch's Name", required=1)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    '''Branch users'''
    user_id = fields.Many2one('res.users', 'Manager User', required=1, domain=lambda self: [("company_id", "in", self.env.user.company_ids.ids)])
    user_ids = fields.Many2many('res.users', 'hotel_restaurant_branch_user_rel', 'branch_id', 'user_id',
                                string='POS Users', domain=lambda self: [("company_id", "in", self.env.user.company_ids.ids)])

    '''POS'''
    hotel_restaurant_pos_ids = fields.One2many('sea.pos.hotel.restaurant', 'hotel_restaurant_branch_id',
                                               string='POS Configs')

    '''Pricing'''
    iface_tax_included = fields.Selection([('subtotal', 'Tax-Excluded Price'), ('total', 'Tax-Included Price')],
                                          string="Tax Display", default='subtotal', required=True)
    available_pricelist_ids = fields.Many2many('product.pricelist', string='Available Pricelists',
                                               default=_default_pricelist)

    '''Order and booking'''
    digit_of_discount = fields.Integer(string="Digits of Discount")

    '''Accounting'''
    # payment_journal_ids = fields.Many2many('account.journal', 'hotel_restaurant_branch_id', string=" Payment
    # Journals", domain=lambda self: [("company_id", "=", self.env.user.company_id.id)], required=True)

    payment_journal_ids = fields.Many2many('account.journal', string='Payment journals')
    invoice_journal_id = fields.Many2one("account.journal", string="Accounting invoice journal",
                                         domain=lambda self: [("company_id", "=", self.env.user.company_id.id)],
                                         required=True)

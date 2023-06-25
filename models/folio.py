from odoo import _, api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, ValidationError


class Folio(models.Model):
    _name = "sea.folio"
    _description = "Hotel and Restaurant Folio"
    _order = "id"

    @api.model
    def _get_current_datetime(self):
        if "checkin" in self._context:
            return self._context["checkin"]
        else:
            now = datetime.now()
            return now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    folio_sequence = fields.Char("Folio sequence", readonly=True, default=lambda self: _('New'), index=True)
    folio_name = fields.Char("Folio Name")
    order_date = fields.Datetime(string="Create Date", required=True, default=_get_current_datetime, readonly=True)
    order_ids = fields.One2many("sale.order", "folio_id")
    customer_id = fields.Many2one("res.partner", string='Customer', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ('inprogress', 'In Progress'),
    ],
        string='Status', default='draft', readonly=True)
    sale_person_id = fields.Many2one("res.partner", string='Sale Person', required=True,
                                     default=lambda self: self.env.user.partner_id.id)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('sea.hotel.restaurant.branch', string="Branch",
                                domain=lambda self: self.domain_branch_by_user(), require=True)
    invoice_id = fields.Many2one("account.invoice", "Invoice", copy=False)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', currency_field='currency_id', store=True, readonly=True,
                                     compute='_compute_total_price', track_visibility='onchange', track_sequence=5)
    amount_tax = fields.Monetary(string='Taxes', currency_field='currency_id', store=True, readonly=True,
                                 compute='_compute_total_price')
    amount_total = fields.Monetary(string='Total', currency_field='currency_id', store=True,
                                   readonly=True, compute='_compute_total_price',
                                   track_visibility='always', track_sequence=6)
    total_discount = fields.Monetary(string='Discount', currency_field='currency_id',
                                     store=True, readonly=True, compute='_compute_total_price',
                                     track_visibility='always')
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    order_current = fields.Many2many("sale.order", string="Order Current")

    @api.multi
    @api.depends("order_ids", "order_ids.amount_total",
                 "order_ids.amount_total")
    def _compute_total_price(self):
        for folio in self:
            amount_untaxed = amount_tax = total_discount = 0.0

            for order in folio.order_ids:
                amount_untaxed += order.amount_untaxed
                amount_tax += order.amount_tax
                total_discount += order.total_discount

            folio.update({
                "amount_untaxed": amount_untaxed,
                "amount_tax": amount_tax,
                "total_discount": total_discount,
                "amount_total": amount_untaxed + amount_tax
            })

    @api.model
    def domain_branch_by_user(self):
        user_branch = []
        branches = self.env["sea.hotel.restaurant.branch"].sudo().search([])
        for branch in branches:
            if self.env.user.partner_id.id in [user.partner_id.id for user in branch.user_ids]:
                user_branch.append(branch.id)
        domain = [("id", "in", user_branch)]
        return domain

    @api.model
    def create(self, vals):
        print('vao create folio', vals)

        if vals.get('folio_sequence', _('New')) == _('New'):
            print('test vals company', vals)
            if 'company_id' in vals:
                vals['folio_sequence'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code(
                    'seatek.folio') or _('New')
            else:
                vals['folio_sequence'] = self.env['ir.sequence'].next_by_code('seatek.folio') or _('New')

        customer_id = self.env["res.partner"].sudo().search([("id", "=", vals["customer_id"])])
        vals["folio_name"] = customer_id.display_name
        if customer_id.phone:
            vals["folio_name"] += " | " + customer_id.phone

        # if "hotel_order_ids" in vals:
        #     for order in vals["hotel_order_ids"]:
        #         order[2]["order_type"] = 'hotel_order'
        #         for order_line in order[2]["order_line"]:
        #             order_line_data = order_line[2]
        #             room = self.env['sea.hotel.room'].sudo().search([("id", "=", order_line_data["room_id"])])
        #             room.write({"status": "occupied", "available": False})
        #
        # if "restaurant_order_ids" in vals:
        #     for order in vals["restaurant_order_ids"]:
        #         order[2]["order_type"] = 'restaurant_order'

        return super(Folio, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            if self.env.context.get("folio_display_name"):
                folio_name = '[' + rec.folio_sequence + ']  ' + rec.folio_name
            else:
                folio_name = rec.folio_sequence
            result.append((rec.id, folio_name))
        return result

    @api.model
    def _name_search(self, folio_name="folio_sequence", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        domain = args + ["|", ("folio_sequence", operator, folio_name), ("folio_name", operator, folio_name)]
        return super(Folio, self).search(domain, limit=limit).name_get()

    @api.multi
    def lock_invoice_temp(self):
        if not self.order_ids:
            raise ValidationError(_("Can't create invoice when hotel order or restaurant order is empty"))
            return
        sale_order_current = self.env['sale.order'].search([("id", "in", self.order_ids.ids), ('state', '!=', 'done')])
        self.order_current = [(6, 0, sale_order_current.ids)]
        print('test sale_order_current', self.order_current)
        for order in sale_order_current:

            if order.room_id:
                order.lock_hotel_order()
            elif order.table_id:
                order.lock_restaurant_order()
        self.state = "done"

    @api.multi
    def unlock_invoice_temp(self):
        if not self.order_ids:
            raise ValidationError(_("Can't create invoice when hotel order or restaurant order is empty"))
            return
        for order in self.order_current:
            order.write({'state': 'sale'})
        self.state = "inprogress"

    @api.multi
    def view_invoice(self):
        sale_orders = self.env["sale.order"].search(
            [("id", "in", self.order_ids.ids)])
        return sale_orders.action_view_invoice()

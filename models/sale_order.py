from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pos_hotel_restaurant_id = fields.Many2one("sea.pos.hotel.restaurant", "Partner")

    order_type = fields.Selection([
        ('hotel_order', 'Is Hotel Order'),
        ('restaurant_order', 'Is Restaurant Order')], string='Order Type')

    folio_id = fields.Many2one("sea.folio", "Folio")

    table_id = fields.Many2one("sea.restaurant.table", "Table Restaurant",
                               domain="[('company_id', '=', company_id), ('status', '=', 'available'),"
                                      "('pos_hotel_restaurant_id', '=', pos_hotel_restaurant_id)]")
    room_id = fields.Many2one("sea.hotel.room", "Room", domain="[('company_id', '=', company_id), ('status', '=', "
                                                               "'available'), ('pos_hotel_restaurant_id', '=', "
                                                               "pos_hotel_restaurant_id)]")
    status_room = fields.Selection([("available", "Available"), ("occupied", "Occupied"),
                                    ("maintained", "Maintained"), ("cleaned", "Cleaned")], String="State Room",
                                   related='room_id.status')
    check_in = fields.Datetime(string='Check In')
    check_out = fields.Datetime(string='Check Out')

    '''"Các trường này dùng để tính thành tiền tổng đơn dựa trên SL đã phục vụ.
     Hiện do thống nhất sẽ tính trên SL đặt nên những trường này chưa cần xài"'''

    # done_untaxed = fields.Monetary(string='Untaxed Amount', currency_field='currency_id', store=True, readonly=True,
    #                                track_visibility='onchange', track_sequence=5)
    # done_taxes = fields.Monetary(string='Taxes', currency_field='currency_id', store=True, readonly=True)
    # done_discount = fields.Monetary(string='Discount', currency_field='currency_id',
    #                                 store=True, readonly=True, track_visibility='always')
    # done_total = fields.Monetary(string='Total', currency_field='currency_id', store=True,
    #                              readonly=True, track_visibility='always', track_sequence=6)
    # currency_id = fields.Many2one('res.currency', string="Currency",
    #                               default=lambda self: self.env.user.company_id.currency_id)

    # @api.multi
    # def set_default_is_hotel_guest(self):
    #     if self.folio_id_restaurant or self.folio_id_hotel:
    #         self.is_hotel_guest = True
    #
    # @api.multi
    # def check_invoice_can_be_pay(self):
    #     pay_ok = True
    #     if not self.invoice_ids:
    #         pay_ok = False
    #     else:
    #         for invoice in self.invoice_ids:
    #             if invoice.state != 'open':
    #                 pay_ok = False
    #                 break
    #     self.can_be_pay = pay_ok
    #
    # is_hotel_guest = fields.Boolean("Is Hotel Guest?", default=False, compute='set_default_is_hotel_guest')
    #
    # can_be_pay = fields.Boolean(default=False, compute='check_invoice_can_be_pay')
    #
    # @api.onchange("pos_hotel_restaurant_id")
    # def domain_pos_by_branch_user(self):
    #     user_branch = []
    #     branches = self.env["sea.hotel.restaurant.branch"].sudo().search([])
    #     for branch in branches:
    #         if self.env.user.partner_id.id in [user.partner_id.id for user in branch.user_ids]:
    #             user_branch.append(branch.id)
    #     domain = [
    #         ("company_id", "=", self.env.user.company_id.id),
    #         ("hotel_restaurant_branch_id", "in", user_branch)
    #     ]
    #     if self.folio_id_hotel:
    #         domain.append(("pos_type", "=", "hotel"))
    #     elif self.folio_id_restaurant:
    #         domain.append(("pos_type", "=", "restaurant"))
    #
    #     field_domain = {"pos_hotel_restaurant_id": domain}
    #     return {"domain": field_domain}
    #
    # @api.onchange("folio_id_restaurant", "folio_id_hotel")
    # def domain_folio_by_branch_user(self):
    #     pos_branch_id = self.pos_hotel_restaurant_id.hotel_restaurant_branch_id.id
    #     domain = [('state', '=', 'draft'), ('branch_id', '=', pos_branch_id)]
    #     field_domain = {"folio_id_restaurant": domain, "folio_id_hotel": domain}
    #     return {"domain": field_domain}
    @api.multi
    def _get_checkin_date(self):
        if "checkin" in self._context:
            return self._context["checkin"]
        else:
            now = datetime.now()
            checkin_date = datetime(now.year, now.month, now.day, 5, 0, 0)
            return checkin_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.multi
    def _get_checkout_date(self):
        if "checkout" in self._context:
            return self._context["checkout"]
        else:
            now = datetime.now()
            checkin_date = datetime(now.year, now.month, now.day, 5, 0, 0)
            checkout_date = checkin_date + timedelta(days=1)
            return checkout_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.multi
    def check_folio_customer(self, partner_id):
        folio_check = self.env['sea.folio'].search([('customer_id', '=', partner_id), ('state', '=', 'inprogress')],
                                                   limit=1)
        if folio_check:
            return folio_check.id
        else:
            return False

    @api.model
    def create(self, vals):
        print(vals)
        if 'check_in' not in vals and 'check_out' not in vals and 'room_id' in vals:
            vals['check_in'] = self._get_checkin_date()
            vals['check_out'] = self._get_checkout_date()
        get_branch_id = self.env['sea.pos.hotel.restaurant'].search([('id', '=', vals.get('pos_hotel_restaurant_id'))])
        if get_branch_id.pos_type == 'hotel':
            folio_id = self.check_folio_customer(vals.get('partner_id'))
            if folio_id:
                vals["folio_id"] = folio_id
            else:
                if vals.get('folio_sequence', _('New')) == _('New'):
                    if 'company_id' in vals:
                        vals['folio_sequence'] = self.env['ir.sequence'].with_context(
                            force_company=vals['company_id']).next_by_code(
                            'seatek.folio') or _('New')
                    else:
                        vals['folio_sequence'] = self.env['ir.sequence'].next_by_code('seatek.folio') or _('New')
                customer_id = self.env["res.partner"].sudo().search([("id", "=", vals["partner_id"])])
                vals["folio_name"] = customer_id.display_name
                if customer_id.phone:
                    vals["folio_name"] += " | " + customer_id.phone
                res = self.env['sea.folio'].sudo().create({'folio_name': vals.get('folio_name'),
                                                           'folio_sequence': vals.get('folio_sequence'),
                                                           'customer_id': vals.get('partner_id'),
                                                           'sale_person_id': self.env.user.partner_id.id,
                                                           'branch_id': get_branch_id.hotel_restaurant_branch_id.id,
                                                           'company_id': vals.get('company_id'),
                                                           'state': 'inprogress'
                                                           })
                vals["folio_id"] = res.id
        rec = super(SaleOrder, self).create(vals)
        if 'room_id' in vals and rec.order_type == 'hotel_order':
            room = self.env['sea.hotel.room'].sudo().search([('id', '=', vals.get('room_id'))])
            if room:
                if room.product_default:
                    self.env['sale.order.line'].sudo().create({'product_id': room.product_default.id,
                                                               'room_id': vals.get('room_id'),
                                                               'order_id': rec.id,
                                                               'checkin_date': self._get_checkin_date(),
                                                               'checkout_date': self._get_checkout_date()
                                                               })
                if room.default_amenities:
                    for default_amenitie in room.default_amenities:
                        self.env['sale.order.line'].sudo().create({'product_id': default_amenitie.product_id.id,
                                                                   'product_uom_qty': default_amenitie.quantity,
                                                                   'room_id': vals.get('room_id'),
                                                                   'order_id': rec.id,
                                                                   })

        return rec

    @api.multi
    def write(self, vals):
        reserved_old = {}
        if 'order_line' in vals:
            for line_values in vals['order_line']:
                if line_values[0] == 1:  # Kiểm tra action là update
                    reserved_old[str(line_values[1])] = self.env['sale.order.line'].browse(line_values[1]).qty_reserved
            rec = super(SaleOrder, self).write(vals)
            for line_values in vals['order_line']:
                if line_values[0] == 1:
                    if self.env['sale.order.line'].browse(line_values[1]).qty_reserved >= reserved_old.get(
                            str(line_values[1])):
                        '''validate'''
                        picking_ids = self.env['stock.picking'].sudo().search(
                            [('state', 'not in', ['done', 'cancel']), ('sale_id', '=', self.id),
                             ('origin', '=', self.name)])
                        if picking_ids:
                            for picking in picking_ids:
                                if self.env['stock.move'].sudo().search(
                                        [('picking_id', '=', picking.id),
                                         ('product_id', '=',
                                          self.env['sale.order.line'].browse(line_values[1]).product_id.id)]):
                                    picking.validate_for_hotel_restaurant()
                    else:
                        '''return'''
                        picking_ids_return = self.env['stock.picking'].sudo().search(
                            [('state', 'not in', ['done', 'cancel']), ('sale_id', '=', self.id),
                             ('origin', '!=', self.name)])
                        if picking_ids_return:
                            for picking_return in picking_ids_return:
                                if self.env['stock.move'].sudo().search(
                                        [('picking_id', '=', picking_return.id),
                                         ('product_id', '=',
                                          self.env['sale.order.line'].browse(line_values[1]).product_id.id)]):
                                    picking_return.validate_return_for_hotel_restaurant()

                                    uom_qty = self.env['sale.order.line'].browse(line_values[1]).product_uom_qty
                                    self.env['sale.order.line'].browse(line_values[1]).write(
                                        {'product_uom_qty': uom_qty - (reserved_old.get(str(line_values[1])) - self.env[
                                            'sale.order.line'].browse(line_values[1]).qty_reserved)})
                                    self.env['sale.order.line'].browse(line_values[1]).write(
                                        {'product_uom_qty': uom_qty})

            return rec
        return super(SaleOrder, self).write(vals)

    #
    # @api.onchange("folio_id_hotel", "folio_id_restaurant")
    # def onchange_folio_id(self):
    #     if self.folio_id_hotel or self.folio_id_restaurant:
    #         if self.folio_id_hotel:
    #             partner = self.env["res.partner"].browse(self.folio_id_hotel.customer_id.id)
    #         else:
    #             partner = self.env["res.partner"].browse(self.folio_id_restaurant.customer_id.id)
    #         self.partner_id = partner.id
    #         self.partner_invoice_id = partner.id
    #         self.partner_shipping_id = partner.id
    #         self.pricelist_id = partner.property_product_pricelist.id
    #
    # @api.onchange("partner_id")
    # def onchange_partner_id(self):
    #     if self.partner_id:
    #         self.partner_invoice_id = self.partner_id.id
    #         self.partner_shipping_id = self.partner_id.id
    #         self.pricelist_id = self.partner_id.property_product_pricelist.id
    #
    #     else:
    #         if self.folio_id_hotel:
    #             partner = self.env["res.partner"].browse(self.folio_id_hotel.customer_id.id)
    #         else:
    #             partner = self.env["res.partner"].browse(self.folio_id_restaurant.customer_id.id)
    #         self.partner_id = partner.id
    #         self.partner_invoice_id = partner.id
    #         self.partner_shipping_id = partner.id
    #         self.pricelist_id = partner.property_product_pricelist.id
    #

    @api.multi
    def confirm_order(self):
        # update all food item in restaurant served
        if self.order_type == "restaurant_order":
            if self.table_id:
                self.table_id.write({"status": "occupied"})

        # update status of rooms is available for sale
        if self.order_type == "hotel_order" and self.order_line:
            for line in self.order_line:
                line.room_id.write({"status": "occupied"})

        # confirm and unlock sale order
        self.action_confirm()
        self.action_unlock()
        '''thực hiện DONE nếu qty_reseved > 0 '''
        for rec in self:
            if rec.order_line:
                pro_ids = []
                for line in rec.order_line:
                    if line.qty_reserved > 0:
                        qty_done = line.qty_reserved
                        pro_ids.append(line.product_id.id)
                        stock_pickings = self.env['stock.picking'].sudo().search(
                            [('sale_id', '=', line.order_id.id), ('state', 'in', ['assigned'])])
                        if stock_pickings:
                            for stock_picking in stock_pickings:
                                if qty_done == 0:
                                    break
                                stock_moves = self.env['stock.move'].sudo().search(
                                    [('picking_id', '=', stock_picking.id),
                                     ('product_id', '=', line.product_id.id)])
                                if stock_moves:
                                    for stock_move in stock_moves:
                                        if qty_done == 0:
                                            break
                                        stock_move_lines = self.env['stock.move.line'].sudo().search(
                                            [('move_id', '=', stock_move.id), ('picking_id', '=', stock_picking.id),
                                             ('product_id', '=', line.product_id.id)])
                                        if stock_move_lines:
                                            for stock_move_line in stock_move_lines:
                                                if qty_done == 0:
                                                    break
                                                else:
                                                    if qty_done >= stock_move_line.product_uom_qty:
                                                        qty_done = qty_done - stock_move_line.product_uom_qty
                                                        stock_move_line.qty_done = stock_move_line.product_uom_qty
                                                    else:
                                                        stock_move_line.qty_done = qty_done
                                                        qty_done = 0
                                '''product có lệnh sx và không có tồn kho'''
                                for stock_move_sx in stock_picking.move_lines.sudo():
                                    if stock_move_sx.quantity_done > 0 \
                                            and stock_move_sx.created_production_id \
                                            and stock_move_sx.sudo().product_id.id == line.product_id.id:
                                        production_id = stock_move_sx.sudo().created_production_id
                                        mrp_product_produce = self.env[
                                            'mrp.product.produce'].sudo().with_context(
                                            active_id=production_id.id).sudo().create(
                                            {'production_id': production_id.id,
                                             'product_id': line.product_id.id,
                                             'product_qty': stock_move_sx.quantity_done})
                                        mrp_product_produce._onchange_product_qty()
                                        mrp_product_produce.do_produce()
                                        production_id.post_inventory()
                                        stock_move_update = self.env['stock.move'].sudo().search(
                                            [('raw_material_production_id', '=', production_id.id),
                                             ('state', 'not in', ['done', 'cancel'])])
                                        for i in stock_move_update:
                                            move_line = self.env['stock.move.line'].sudo().search(
                                                [('move_id', '=', i.id), ('state', 'not in', ['done', 'cancel'])])
                                            for line_ in move_line:
                                                if line_.product_uom_qty < 0:
                                                    line_.product_uom_qty = 0

                '''validate'''
                picking_ids = self.env['stock.picking'].sudo().search(
                    [('state', 'not in', ['done', 'cancel']), ('sale_id', '=', self.id),
                     ('origin', '=', self.name)])
                if picking_ids:
                    for picking in picking_ids:
                        if self.env['stock.move'].sudo().search(
                                [('picking_id', '=', picking.id),
                                 ('product_id', 'in', pro_ids)]):
                            picking.validate_for_hotel_restaurant()

    @api.multi
    def unlock_sale_order(self):
        self.action_unlock()
        if self.table_id:
            self.table_id.status = 'occupied'
        elif self.room_id:
            self.room_id.status = 'occupied'

    @api.multi
    def lock_restaurant_order(self):
        if self.order_type == "restaurant_order":
            if self.order_line:
                for line in self.order_line:
                    '''cập nhật lại product_uom_qty = qty_delivered'''
                    line.product_uom_qty = line.qty_delivered
            if self.table_id:
                self.table_id.status = 'available'
        self.action_done()
        if self.order_type == "restaurant_order":
            if self.order_line:
                for line in self.order_line:
                    '''cập nhật lại qty_reserved = qty_delivered'''
                    line.qty_reserved = line.qty_delivered

    @api.multi
    def lock_hotel_order(self):
        if self.order_type == "hotel_order":
            if self.order_line:
                for line in self.order_line:
                    '''cập nhật lại product_uom_qty = qty_delivered'''
                    line.product_uom_qty = line.qty_delivered
            if self.room_id:
                self.room_id.status = 'cleaned'
        self.action_done()
        if self.order_type == "hotel_order":
            if self.order_line:
                for line in self.order_line:
                    '''cập nhật lại qty_reserved = qty_delivered'''
                    line.qty_reserved = line.qty_delivered

    @api.multi
    def cleaned_room(self):
        if self.room_id:
            self.room_id.status = 'available'

    # @api.multi
    # def validate_sale_order(self):
    #     # excluding inventory
    #     stock_picking = self.env["stock.picking"].sudo().search([('sale_id', '=', self.id)], limit=1)
    #     if stock_picking:
    #         # ########### HoDu ###############
    #         # change location of stock move lines to location config
    #         if self.pos_hotel_restaurant_id.stock_location_id:
    #             # stock_picking.location_id = self.pos_hotel_restaurant_id.stock_location_id
    #             for stock_move in stock_picking.move_lines:
    #                 stock_move.location_id = self.pos_hotel_restaurant_id.stock_location_id
    #                 for stock_move_line in stock_move.move_line_ids:
    #                     stock_move_line.location_id = self.pos_hotel_restaurant_id.stock_location_id
    #         # ################################
    #         # Action fill up stock move line
    #         stock_picking.action_pack_operation_auto_fill()
    #         stock_picking.button_validate()
    #
    #     # crate invoice if it not include folio
    #     if not self.folio_id_hotel and not self.folio_id_restaurant:
    #         sale_orders = self.env["sale.order"].browse(self.id)
    #         # Action create invoice from sale order
    #         invoice_id = sale_orders.action_invoice_create()
    #         invoice = self.env["account.invoice"].browse(invoice_id[0])
    #         # Action validate invoice
    #         invoice.action_invoice_open()
    #
    #         # open form payment from module account
    #         invoice_id = self.invoice_ids.id
    #         branch_id = self.pos_hotel_restaurant_id.hotel_restaurant_branch_id.id
    #         return {
    #             'name': 'Register Payment',
    #             'type': 'ir.actions.client',
    #             'tag': 'payment_view',
    #             'target': 'new',
    #             'context': {"invoice_id": invoice_id, "branch_id": branch_id}
    #         }
    #
    # @api.multi
    # def open_account_payment_view(self):
    #     invoice_id = self.invoice_ids.id
    #     branch_id = self.pos_hotel_restaurant_id.hotel_restaurant_branch_id.id
    #
    #     # open form payment from module account
    #     return {
    #         'name': 'Register Payment',
    #         'type': 'ir.actions.client',
    #         'tag': 'payment_view',
    #         'target': 'new',
    #         'context': {"invoice_id": invoice_id, "branch_id": branch_id}
    #     }
    #

    @api.multi
    def action_open_folio_view(self):
        # if self.folio_id_hotel:
        #     folio = self.folio_id_hotel
        # elif self.folio_id_restaurant:
        #     folio = self.folio_id_restaurant
        if self.folio_id:
            return {
                'name': _(self.folio_id.folio_name),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sea.folio',
                'view_id': self.env.ref('sea_hotel_restaurant.view_hotel_folio_form').id,
                'type': 'ir.actions.act_window',
                'res_id': self.folio_id.id,
                'target': 'current',
            }
        else:
            return True

    @api.multi
    def pool_table(self):
        context = dict(self._context)
        context.update({'order_id_parent': self.table_id.id})
        view = self.env.ref('sea_hotel_restaurant.view_table_virtual_form')
        return {
            'name': 'Chọn bàn để gộp',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'table.virtual',
            'view_id': view.id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def move_table(self):
        context = dict(self._context)
        context.update({'move_order_id_parent': self.table_id.id})
        view = self.env.ref('sea_hotel_restaurant.view_move_table_virtual_form')
        return {
            'name': 'Chọn bàn để chuyển',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'table.virtual.many2one',
            'view_id': view.id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def move_room(self):
        context = dict(self._context)
        context.update({'room_id_parent': self.room_id.id})
        view = self.env.ref('sea_hotel_restaurant.view_move_room_virtual_form')
        return {
            'name': 'Chọn phòng để chuyển',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'table.virtual.many2one',
            'view_id': view.id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class TableVirtual(models.TransientModel):
    _name = 'table.virtual'
    _description = 'Table Virtual To Test'

    table_id_pool = fields.Many2many('sea.restaurant.table', string='Bàn sẽ gộp ')
    order_id_parent = fields.Char(string="Table ID Bàn gốc", default=lambda self: self._context.get('order_id_parent'))

    @api.model
    def create(self, vals):
        vals["order_id_parent"] = self._context.get('order_id_parent')

        order_id_parent = self.env["sale.order"].sudo().search(
            [('table_id', '=', vals.get('order_id_parent')), ('state', 'in', ['draft', 'sent', 'sale'])])
        '''Kiem tra xem neu nhu gop ban co partner_id khac nhau thi bao loi'''
        reference_partner_id = order_id_parent.partner_id.id
        for table_id_children in vals.get('table_id_pool')[0][2]:
            if table_id_children:
                check_partner_id = self.env["sale.order"].sudo().search([
                    ('table_id', '=', table_id_children),
                    ('state', 'in', ['draft', 'sent', 'sale'])
                ])
                if reference_partner_id == False or check_partner_id.partner_id.id == False:
                    raise UserError(_('Empty Tables Cannot Be Combined'))

        ''' Lay children '''
        for table_id_children in vals.get('table_id_pool')[0][2]:
            if table_id_children:
                order_id_children = self.env["sale.order"].sudo().search(
                    [('table_id', '=', table_id_children), ('state', 'in', ['draft', 'sent', 'sale'])])
                order_id_children_line = self.env["sale.order.line"].sudo().search(
                    [('order_id', '=', order_id_children.id)])
                for order_line in order_id_children_line:
                    change_origin_stock_move = self.env["stock.move"].sudo().search(
                        [('sale_line_id', '=', order_line.id)])
                    origin_old_to_get_rpm_production = False
                    change_sale_id_picking = self.env["stock.picking"].sudo().search(
                        [('sale_id', '=', order_id_children.id)])
                    for picking_change in change_sale_id_picking:
                        picking_change.write({'sale_id': order_id_parent.id,
                                              'origin': order_id_parent.name
                                              })
                    for stock_move in change_origin_stock_move:
                        origin_old_to_get_rpm_production = stock_move.origin
                        stock_move.write({'origin': order_id_parent.name})

                    if origin_old_to_get_rpm_production != False:

                        change_origin_mrp_production = self.env["mrp.production"].sudo().search(
                            [('origin', '=', origin_old_to_get_rpm_production)])

                        if change_origin_mrp_production:
                            for mrp_production in change_origin_mrp_production:
                                mrp_production.write({'origin': order_id_parent.name})

                    order_line.write({'order_id': order_id_parent.id})
                order_id_parent.write(
                    {'amount_untaxed': order_id_parent.amount_untaxed + order_id_children.amount_untaxed,
                     'amount_tax': order_id_parent.amount_tax + order_id_children.amount_tax,
                     'amount_total': (order_id_parent.amount_untaxed + order_id_children.amount_untaxed)
                                     + (order_id_parent.amount_tax + order_id_children.amount_tax)
                     })

                vals["order_id_children"] = order_id_children.id
                order_id_children.write({'state': 'cancel'})
                return_availeble_table = self.env["sea.restaurant.table"].sudo().search(
                    [('id', '=', table_id_children)])
                return_availeble_table.write({'status': 'available'})

        record = super(TableVirtual, self).create(vals)
        return record


class TableVirtualMany2one(models.TransientModel):
    _name = 'table.virtual.many2one'
    _description = 'Table Virtual Many2one To Test'

    table_id_pool = fields.Many2one('sea.restaurant.table', string='Bàn sẽ gộp ')
    order_id_parent = fields.Char(string="Table ID Bàn gốc", readonly=True)
    order_line = fields.Many2many('sale.order.line', string='Danh sách món gộp', domain="[]")
    room_id = fields.Many2one('sea.hotel.room', string='Phòng sẽ gộp ')
    room_id_parent = fields.Char(string="Room ID phòng gốc", readonly=True)

    @api.onchange("room_id")
    def set_default_room_id_parent(self):
        if self.room_id:
            self.room_id_parent = self._context.get('room_id_parent')

    @api.onchange("table_id_pool")
    def set_default_table_domain(self):
        if self.table_id_pool:
            self.order_id_parent = self._context.get('move_order_id_parent')

    @api.model
    def create(self, vals):
        # print('test vals cua many2one', vals )

        record = super(TableVirtualMany2one, self).create(vals)

        if self._context.get('room_id_parent'):
            vals["room_id_parent"] = self._context.get('room_id_parent')
            order_id_parent = self.env["sale.order"].sudo().search(
                [('room_id', '=', vals.get('room_id_parent')), ('state', 'in', ['draft', 'sent', 'sale'])])
            order_id_parent.write({'room_id': vals.get('room_id')})
            if vals.get('room_id'):
                room = self.env['sea.hotel.room'].sudo().search([('id', '=', vals.get('room_id'))])
                if room:
                    if room.product_default:
                        self.env['sale.order.line'].sudo().create({'product_id': room.product_default.id,
                                                                   'room_id': vals.get('room_id'),
                                                                   'order_id': order_id_parent.id,
                                                                   'checkin_date': order_id_parent._get_checkin_date(),
                                                                   'checkout_date': order_id_parent._get_checkout_date()})
                    if room.default_amenities:
                        for default_amenitie in room.default_amenities:
                            self.env['sale.order.line'].sudo().create({'product_id': default_amenitie.product_id.id,
                                                                       'product_uom_qty': default_amenitie.quantity,
                                                                       'room_id': vals.get('room_id'),
                                                                       'order_id': order_id_parent.id,
                                                                       'checkin_date': order_id_parent._get_checkin_date(),
                                                                       'checkout_date': order_id_parent._get_checkout_date()
                                                                       })

            return_occupied_room = self.env["sea.hotel.room"].sudo().search(
                [('id', '=', vals.get('room_id'))])
            return_occupied_room.write({'status': 'occupied'})
            return_availeble_room = self.env["sea.hotel.room"].sudo().search(
                [('id', '=', vals.get('room_id_parent'))])
            return_availeble_room.write({'status': 'available'})

        elif self._context.get('move_order_id_parent'):
            vals["order_id_parent"] = self._context.get('move_order_id_parent')
            order_id_parent = self.env["sale.order"].sudo().search(
                [('table_id', '=', vals.get('order_id_parent')), ('state', 'in', ['draft', 'sent', 'sale'])])
            order_id_parent.write({'table_id': vals.get('table_id_pool')})
            #  Phan nay duoi cung
            return_occupied_table = self.env["sea.restaurant.table"].sudo().search(
                [('id', '=', vals.get('table_id_pool'))])
            return_occupied_table.write({'status': 'occupied'})
            return_availeble_table = self.env["sea.restaurant.table"].sudo().search(
                [('id', '=', vals.get('order_id_parent'))])
            return_availeble_table.write({'status': 'available'})

        # if vals.get('table_id_pool'):
        #     new_sale_order = order_id_parent.copy({
        #         'order_line': [],
        #         'table_id': vals.get('table_id_pool'),
        #     })
        # order_id_parent_line = self.env["sale.order.line"].sudo().search(
        #         [('order_id', '=', order_id_parent.id)])
        #
        # for order_line in order_id_parent_line:
        #     change_origin_stock_move = self.env["stock.move"].sudo().search(
        #         [('sale_line_id', '=', order_line.id)])
        #     origin_old_to_get_rpm_production = False
        #     change_sale_id_picking = self.env["stock.picking"].sudo().search(
        #         [('sale_id', '=', order_id_parent.id)])
        #     for picking_change in change_sale_id_picking:
        #         picking_change.write({'sale_id': new_sale_order.id,
        #                               'origin': new_sale_order.name
        #                               })
        #     for stock_move in change_origin_stock_move:
        #         origin_old_to_get_rpm_production = stock_move.origin
        #         stock_move.write({'origin': new_sale_order.name})
        #
        #     if origin_old_to_get_rpm_production != False:
        #
        #         change_origin_mrp_production = self.env["mrp.production"].sudo().search(
        #             [('origin', '=', origin_old_to_get_rpm_production)])
        #
        #         if change_origin_mrp_production:
        #             for mrp_production in change_origin_mrp_production:
        #                 mrp_production.write({'origin': new_sale_order.name})
        #
        #     order_line.write({'order_id': new_sale_order.id})
        # vals["order_id_children"] = new_sale_order.id
        # order_id_parent.write({'state': 'cancel'})

        # else:
        #     vals["order_id_parent"] = self._context.get('order_id_parent')
        #     order_id_parent = self.env["sale.order"].sudo().search(
        #         [('table_id', '=', vals.get('order_id_parent')), ('state', 'in', ['draft', 'sent', 'sale'])])
        #     print('test vals',vals)
        #
        #     state_old = order_id_parent.state
        #     fillter_sale_line = self.env["sale.order.line"].sudo().search(
        #         [('id', 'in', vals.get('order_line')[0][2])])
        #
        #     new_sale_order = order_id_parent.copy({
        #         'order_line': [(4, i.id , False) for i in fillter_sale_line],
        #         'table_id': vals.get('table_id_pool'),
        #     })

        # order_id_parent.write({'state': 'draft'})
        # new_sale_order.write({'state': 'draft'})
        # remove_sale_line_parent = self.env["sale.order.line"].sudo().search(
        #     [('order_id', '=', order_id_parent.id), ('id', 'in', vals.get('order_line')[0][2])])
        # remove_sale_line_children = self.env["sale.order.line"].sudo().search(
        #     [('order_id', '=', new_sale_order.id)])
        # remove_sale_line_parent.unlink()
        # check_remove_new = self.env["sale.order.line"].sudo().search(
        #     [('order_id', '=', order_id_parent.id)])
        # print('test check_remove_new ', check_remove_new)
        #
        # for parent in check_remove_new:
        #     print('test parent for 1')
        #     print('test parent for 1 parent----------------', parent.product_id)
        #
        #     for remove in remove_sale_line_children:
        #          print('test  remove_sale_line_children for 2')
        #          print('test remove for 2 remove', remove)
        #          if parent.product_id.id == remove.product_id.id and parent.product_uom_qty == remove.product_uom_qty and parent.qty_reserved == remove.qty_reserved:
        #              print('print if 1')
        #              remove.sudo().unlink()
        #
        #          elif parent.product_id.id == remove.product_id.id and parent.product_uom_qty == remove.product_uom_qty:
        #              print('print if 2')
        #              remove.unlink()
        #
        #          elif parent.product_id.id == remove.product_id.id:
        #              print('print if 3')
        #              remove.unlink()
        #
        # print('424')
        # return_occupied_table = self.env["sea.restaurant.table"].sudo().search(
        #     [('id', '=', vals.get('table_id_pool'))])
        # print('427')
        # # return_occupied_table.write({'status': 'occupied'})
        # # order_id_parent.write({'state': state_old})
        # # new_sale_order.write({'state': state_old})
        #
        # print('test new_sale_order', new_sale_order)
        # # print('test remove_sale_line_parent', remove_sale_line_parent)
        # print('test remove_sale_line_children', remove_sale_line_children)
        # print('test return_occupied_table', return_occupied_table)
        return record

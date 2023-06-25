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
    state_folio = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ('inprogress', 'In Progress'),
    ], related='folio_id.state')

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
    partner_id_hr = fields.Many2one('res.partner', string='Partner Hotel Restaurant')

    @api.onchange('partner_id_hr')
    def onchange_partner_id_hr(self):
        self.partner_id = self.partner_id_hr
        self.onchange_partner_id()

    @api.constrains('partner_id_hr')
    def constraint_partner_id_hr(self):
        if self.partner_id_hr:
            self.partner_id = self.partner_id_hr
            self.onchange_partner_id()
            check_folio_partner_old = self.env['sea.folio'].sudo().search(
                [('id', '=', self.folio_id.id)], limit=1)
            check_folio_partner_new = self.env['sea.folio'].sudo().search(
                [('customer_id', '=', self.partner_id_hr.id), ('state', '=', 'inprogress'),
                 ('branch_id', '=', self.pos_hotel_restaurant_id.hotel_restaurant_branch_id.id)], limit=1)
            if check_folio_partner_new.id != check_folio_partner_old.id:
                if check_folio_partner_new and len(check_folio_partner_old) < 1:
                    self.folio_id = check_folio_partner_new.id

                elif len(check_folio_partner_new) < 1 and check_folio_partner_old:
                    if len(check_folio_partner_old.order_ids) > 1:
                        res = self.env['sea.folio'].sudo().create({
                            'customer_id': self.partner_id_hr.id,
                            'sale_person_id': self.env.user.partner_id.id,
                            'branch_id': self.pos_hotel_restaurant_id.hotel_restaurant_branch_id.id,
                            'company_id': self.company_id.id,
                            'state': 'inprogress'
                        })

                        self.folio_id = res.id
                    if len(check_folio_partner_old.order_ids) == 1:
                        update_folio = self.env['sea.folio'].sudo().search(
                            [('id', '=', self.folio_id.id)])
                        update_folio.write({'customer_id': self.partner_id_hr.id,
                                            'folio_name': self.partner_id_hr.name})
                elif check_folio_partner_new and check_folio_partner_old:
                    if len(check_folio_partner_old.order_ids) > 1:
                        for order in check_folio_partner_new:
                            self.folio_id = order.id

                    if len(check_folio_partner_old.order_ids) == 1:
                        for order in check_folio_partner_new:
                            self.folio_id = order.id
                        for folio in check_folio_partner_old:
                            folio.write({'state', '=', 'cancel'})

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
            return {'folio_id': folio_check.id,
                    'branch_id': folio_check.branch_id.id}
        else:
            return False

    @api.model
    def create(self, vals):
        if 'check_in' not in vals and 'check_out' not in vals and 'room_id' in vals:
            vals['check_in'] = self._get_checkin_date()
            vals['check_out'] = self._get_checkout_date()
        get_branch_id = self.env['sea.pos.hotel.restaurant'].search([('id', '=', vals.get('pos_hotel_restaurant_id'))])
        if get_branch_id.pos_type == 'hotel':
            folio_id = self.check_folio_customer(vals.get('partner_id'))
            if folio_id:
                if folio_id.get("branch_id") == get_branch_id.hotel_restaurant_branch_id.id:
                    print('test vals folio_id', folio_id)
                    vals["folio_id"] = folio_id.get("folio_id")
            else:
                res = self.env['sea.folio'].sudo().create({'customer_id': vals.get('partner_id'),
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
                get_order_line = vals.get('order_line')
                if get_order_line:
                    if room.product_default:
                        count = 0
                        product_uom_qty = 1
                        for product in get_order_line:
                            get_sale_order_line = self.env['sale.order.line'].search(
                                [('order_id', '=', rec.id), ('product_id', '=', product[2].get('product_id'))])
                            if room.product_default.id == int(product[2].get('product_id')):
                                count = int(product[2].get('product_id'))
                                get_sale_order_line.sudo().write({
                                    'product_uom_qty': product_uom_qty + int(product[2].get('product_uom_qty')),
                                    'checkin_date': self._get_checkin_date(),
                                    'checkout_date': self._get_checkout_date()
                                })
                        if count == 0:
                            self.env['sale.order.line'].sudo().create({'product_id': room.product_default.id,
                                                                       'room_id': vals.get('room_id'),
                                                                       'order_id': rec.id,
                                                                       'checkin_date': self._get_checkin_date(),
                                                                       'checkout_date': self._get_checkout_date()
                                                                       })
                    if room.default_amenities:
                        for default_amenitie in room.default_amenities:
                            count_amenitie = 0
                            get_sale_order = self.env['sale.order.line'].search(
                                    [('order_id', '=', rec.id), ('product_id', '=', default_amenitie.product_id.id)])
                            for product in get_order_line:
                                if default_amenitie.product_id.id == int(product[2].get('product_id')):
                                    count_amenitie = count_amenitie + 1
                                    get_sale_order.write({
                                        'product_uom_qty': int(product[2].get('product_uom_qty')) + default_amenitie.quantity,
                                        })
                            if count_amenitie < 1:
                                self.env['sale.order.line'].sudo().create(
                                    {'product_id': default_amenitie.product_id.id,
                                     'product_uom_qty': default_amenitie.quantity,
                                     'room_id': vals.get('room_id'),
                                     'order_id': rec.id,
                                     })
                else:
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
    print('vals', vals)
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
        if self.folio_id:
            self.folio_id.state = 'inprogress'
    elif self.room_id:
        self.room_id.status = 'occupied'
        if self.folio_id:
            self.folio_id.state = 'inprogress'


@api.multi
def lock_restaurant_order(self):
    if self.order_type == "restaurant_order":
        if self.folio_id:
            if len(self.folio_id.order_ids) == 1:
                self.folio_id.state = 'done'
            elif len(self.folio_id.order_ids) > 1:
                temp = 0
                for order_id in self.folio_id.order_ids:
                    if order_id.state == 'done':
                        temp = temp + 1
                if temp == len(self.folio_id.order_ids) - 1:
                    self.folio_id.state = 'done'
        if self.order_line:

            for line in self.order_line:
                check_service = self.env['product.product'].sudo().search(
                    [('id', '=', line.product_id.id)])
                if check_service.product_tmpl_id.type != 'service':
                    '''cập nhật lại product_uom_qty = qty_delivered'''
                    line.product_uom_qty = line.qty_delivered
                if check_service.product_tmpl_id.type == 'service':
                    line.product_uom_qty = line.qty_reserved

        if self.table_id:
            self.table_id.status = 'available'
    self.action_done()
    if self.order_type == "restaurant_order":
        if self.order_line:
            for line in self.order_line:
                '''cập nhật lại qty_reserved = qty_delivered'''
                check_service = self.env['product.product'].sudo().search(
                    [('id', '=', line.product_id.id)])
                if check_service.product_tmpl_id.type != 'service':
                    line.qty_reserved = line.qty_delivered


@api.multi
def lock_hotel_order(self):
    if self.order_type == "hotel_order":
        if self.folio_id:
            if len(self.folio_id.order_ids) == 1:
                self.folio_id.state = 'done'
            elif len(self.folio_id.order_ids) > 1:
                temp = 0
                for order_id in self.folio_id.order_ids:
                    if order_id.state == 'done':
                        temp = temp + 1
                if temp == len(self.folio_id.order_ids) - 1:
                    self.folio_id.state = 'done'
        if self.order_line:
            for line in self.order_line:
                check_service = self.env['product.product'].sudo().search(
                    [('id', '=', line.product_id.id)])
                if check_service.product_tmpl_id.type != 'service':
                    '''cập nhật lại product_uom_qty = qty_delivered'''
                    line.product_uom_qty = line.qty_delivered
                if check_service.product_tmpl_id.type == 'service':
                    line.product_uom_qty = line.qty_reserved
        if self.room_id:
            self.room_id.status = 'cleaned'
    self.action_done()
    if self.order_type == "hotel_order":
        if self.order_line:
            for line in self.order_line:
                '''cập nhật lại qty_reserved = qty_delivered'''
                check_service = self.env['product.product'].sudo().search(
                    [('id', '=', line.product_id.id)])
                if check_service.product_tmpl_id.type != 'service':
                    line.qty_reserved = line.qty_delivered


@api.multi
def cleaned_room(self):
    if self.room_id:
        self.room_id.status = 'available'


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
    context.update({'order_id_parent': self.table_id.id,
                    'company_id': self.company_id.id,
                    'pos_hotel_restaurant': self.pos_hotel_restaurant_id.id})
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
    context.update({'move_order_id_parent': self.table_id.id,
                    'company_id': self.company_id.id,
                    'pos_hotel_restaurant': self.pos_hotel_restaurant_id.id})
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
    context.update({'room_id_parent': self.room_id.id,
                    'company_id': self.company_id.id,
                    'pos_hotel_restaurant': self.pos_hotel_restaurant_id.id})
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
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self._context.get('company_id'))
    pos_hotel_restaurant_id = fields.Many2one('sea.pos.hotel.restaurant', string='Point of Sale', require=True,
                                              default=lambda self: self._context.get('pos_hotel_restaurant'))

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
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self._context.get('company_id'))
    pos_hotel_restaurant_id = fields.Many2one('sea.pos.hotel.restaurant', string='Point of Sale', require=True,
                                              default=lambda self: self._context.get('pos_hotel_restaurant'))

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
            return_occupied_table = self.env["sea.restaurant.table"].sudo().search(
                [('id', '=', vals.get('table_id_pool'))])
            return_occupied_table.write({'status': 'occupied'})
            return_availeble_table = self.env["sea.restaurant.table"].sudo().search(
                [('id', '=', vals.get('order_id_parent'))])
            return_availeble_table.write({'status': 'available'})

        return record

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    '''chưa check'''

    # @api.multi
    # def _get_checkin_date(self):
    #     if "checkin" in self._context:
    #         return self._context["checkin"]
    #     else:
    #         now = datetime.now()
    #         checkin_date = datetime(now.year, now.month, now.day, 5, 0, 0)
    #         return checkin_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #
    # @api.multi
    # def _get_checkout_date(self):
    #     if "checkout" in self._context:
    #         return self._context["checkout"]
    #     else:
    #         now = datetime.now()
    #         checkin_date = datetime(now.year, now.month, now.day, 5, 0, 0)
    #         checkout_date = checkin_date + timedelta(days=1)
    #         return checkout_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    # @api.multi
    # def _compute_table_list(self):
    #     for rec in self:
    #         rec.table_list = rec.order_id.table_list

    @api.multi
    def _compute_tax_list(self):
        for rec in self:
            rec.taxes_id = rec.product_id.product_tmpl_id.taxes_id

    qty_reserved = fields.Float(string="Quantity Done", default=0.0)
    checkin_date = fields.Datetime(string="Check In")
    checkout_date = fields.Datetime(string="Check Out", )
    room_id = fields.Many2one("sea.hotel.room", string="Room No",
                              domain=lambda self: [("company_id", "=", self.env.user.company_id.id)])
    # table_list = fields.Many2many("sea.restaurant.table", string="Table List", compute="_compute_table_list")
    taxes_id = fields.Many2many("account.tax", string="Taxes", compute="_compute_tax_list")

    @api.constrains("checkin_date", "checkout_date")
    def check_dates(self):
        if self.checkin_date and self.checkout_date:
            if self.checkin_date >= self.checkout_date:
                raise ValidationError(
                    _(
                        "Room line Check In Date Should be \
                    less than the Check Out Date!"
                    )
                )

    @api.onchange("room_id")
    def room_id_change(self):
        """
-        @param self: object pointer
-       """
        if self.room_id and self.room_id.product_default and self.order_id.partner_id:
            self.product_id = self.room_id.product_default
            # self.checkin_date = self._get_checkin_date()
            # self.checkout_date = self._get_checkout_date()
            super(SaleOrderLine, self).product_id_change()
            domain = {"product_id": [("id", "in", self.room_id.product_ids.ids)]}
            return {"domain": domain}

    @api.onchange("checkin_date", "checkout_date")
    def calculate_total_date(self):
        if self.checkin_date and self.checkout_date:
            dur = self.checkout_date - self.checkin_date
            sec_dur = dur.seconds
            if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                myduration = dur.days
            else:
                myduration = dur.days + 1
            self.product_uom_qty = myduration

    @api.model
    def create(self, vals):
        # print("order line", vals)
        # if 'checkin_date' not in vals and 'checkout_date' not in vals and 'room_id' in vals:
            # vals['checkin_date'] = self._get_checkin_date()
            # vals['checkout_date'] = self._get_checkout_date()
            # super(SaleOrderLine, self).product_id_change()
        order = self.env['sale.order'].sudo().search([('id', '=', vals.get('order_id'))])
        if order:
            if order.order_type:
                if 'product_id' in vals:
                    check_consu_product = self.env["product.product"].sudo().search(
                        [("id", "=", vals.get('product_id'))])
                    if check_consu_product and check_consu_product.product_tmpl_id.type != 'service':
                        # if check_consu_product.product_tmpl_id.type == 'product' \
                        #             or check_consu_product.product_tmpl_id.type == 'consu':
                        cr = self.env.cr
                        get_infor_pos = self.env["sale.order"].sudo().search([("id", "=", vals.get('order_id'))])
                        default_route = get_infor_pos.pos_hotel_restaurant_id.default_route_id.id
                        custom_route = get_infor_pos.pos_hotel_restaurant_id.custom_routes_id.ids
                        result = False
                        if custom_route:
                            product_product = self.env['product.product'].sudo().search(
                                [('id', '=', vals.get('product_id'))])
                            if product_product:
                                if product_product.product_tmpl_id:
                                    cr.execute(
                                        "SELECT * FROM stock_route_product WHERE product_id = %s and route_id IN %s",
                                        (product_product.product_tmpl_id.id, tuple(custom_route)))
                                    result = cr.fetchall()
                        if result:
                            vals["route_id"] = result[0][0]
                        else:
                            vals["route_id"] = default_route

        return super(SaleOrderLine, self).create(vals)

    @api.multi
    def write(self, values):
        quantity_done_old = self.qty_reserved
        rec = super(SaleOrderLine, self).write(values)
        '''còn trường hợp stock_move_line None sẽ phải tự tạo'''
        if 'qty_reserved' in values and self.state not in ['done', 'cancel']:
            '''qty_done nhỏ hơn product_uom_qty'''
            if 0 > values.get('qty_reserved') or values.get('qty_reserved') > self.product_uom_qty:
                raise UserError(_("SL Done lớn hơn 0 và nhỏ hơn SL đặt."))
            elif quantity_done_old > values.get('qty_reserved'):
                quantity_return = quantity_done_old - values.get('qty_reserved')
                pickings = self.env['stock.picking'].sudo().search(
                    [('sale_id', '=', self.order_id.id), ('state', 'in', ['done']),
                     ('origin', '=', self.order_id.name)])
                if pickings:
                    for picking in pickings:
                        if quantity_return == 0:
                            break
                        stock_moves = self.env['stock.move'].sudo().search(
                            [('picking_id', '=', picking.id),
                             ('product_id', '=', self.product_id.id)])
                        if stock_moves:
                            new_return_picking = self.env['stock.return.picking'].sudo().with_context(
                                active_id=picking.id).create({})
                            if new_return_picking.product_return_moves:
                                temp = quantity_return
                                for product_return in new_return_picking.product_return_moves:
                                    if product_return.product_id.id == self.product_id.id and temp > 0:
                                        if product_return.quantity < temp:
                                            temp -= product_return.quantity
                                        else:
                                            product_return.quantity = temp
                                            temp = 0
                                    else:
                                        product_return.sudo().unlink()
                            new_return_picking._create_returns()

                            picking_rs = self.env['stock.picking'].sudo().search(
                                [('state', 'not in', ['done', 'cancel']),
                                 ('origin', '=', "Return of %s" % new_return_picking.picking_id.name)])
                            if picking_rs:
                                for picking_r in picking_rs:
                                    stock_moves_return = self.env['stock.move'].sudo().search(
                                        [('picking_id', '=', picking_r.id),
                                         ('product_id', '=', self.product_id.id)])
                                    for stock_move in stock_moves_return:
                                        stock_move_lines_return = self.env['stock.move.line'].sudo().search(
                                            [('move_id', '=', stock_move.id), ('picking_id', '=', picking_r.id),
                                             ('product_id', '=', self.product_id.id)])
                                        if stock_move_lines_return:
                                            for stock_move_line_r in stock_move_lines_return:
                                                if quantity_return > 0:
                                                    if quantity_return > stock_move_line_r.product_uom_qty:
                                                        quantity_return -= stock_move_line_r.product_uom_qty
                                                        stock_move_line_r.qty_done = stock_move_line_r.product_uom_qty
                                                    else:
                                                        stock_move_line_r.qty_done = quantity_return
                                                        quantity_return = 0
                                                else:
                                                    stock_move_line_r.sudo().unlink()
            elif quantity_done_old < values.get('qty_reserved'):
                # qty_done = values.get('qty_reserved')
                qty_done = values.get('qty_reserved') - quantity_done_old
                # product = self.env['sale.order.line'].sudo().search(
                #     [('product_id', '=', self.product_id.id), ('order_id', '=', self.order_id.id),
                #      ('id', '!=', self.id)])
                # for i in product:
                #     qty_done += i.qty_reserved

                # stock_pickings = self.env['stock.picking'].sudo().search(
                #     [('sale_id', '=', self.order_id.id), ('state', 'in', ['done', 'assigned'])], order='state desc')
                stock_pickings = self.env['stock.picking'].sudo().search(
                    [('sale_id', '=', self.order_id.id), ('state', 'in', ['assigned'])])
                if stock_pickings:
                    for stock_picking in stock_pickings:
                        if qty_done == 0:
                            break

                        stock_moves = self.env['stock.move'].sudo().search(
                            [('picking_id', '=', stock_picking.id),
                             ('product_id', '=', self.product_id.id)])
                        if stock_moves:
                            for stock_move in stock_moves:
                                if qty_done == 0:
                                    break

                                stock_move_lines = self.env['stock.move.line'].sudo().search(
                                    [('move_id', '=', stock_move.id), ('picking_id', '=', stock_picking.id),
                                     ('product_id', '=', self.product_id.id)])
                                if stock_move_lines:
                                    for stock_move_line in stock_move_lines:
                                        if qty_done == 0:
                                            break

                                        # elif stock_picking.state in ['done']:
                                        #     qty_done = qty_done - stock_move_line.qty_done
                                        else:
                                            if qty_done >= stock_move_line.product_uom_qty:
                                                qty_done = qty_done - stock_move_line.product_uom_qty
                                                stock_move_line.qty_done = stock_move_line.product_uom_qty
                                            else:
                                                stock_move_line.qty_done = qty_done
                                                qty_done = 0
                        # if stock_picking.state not in ['done']:
                        '''product có lệnh sx và không có tồn kho'''
                        for stock_move_sx in stock_picking.move_lines.sudo():
                            if stock_move_sx.quantity_done > 0 \
                                    and stock_move_sx.created_production_id \
                                    and stock_move_sx.sudo().product_id.id == self.product_id.id:
                                production_id = stock_move_sx.sudo().created_production_id
                                mrp_product_produce = self.env[
                                    'mrp.product.produce'].sudo().with_context(
                                    active_id=production_id.id).sudo().create({'production_id': production_id.id,
                                                                               'product_id': self.product_id.id,
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
                                    for line in move_line:
                                        if line.product_uom_qty < 0:
                                            line.product_uom_qty = 0

        return rec


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def validate_for_hotel_restaurant(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
                                 self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(
            float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(
                _('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(
                            _('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        '''chưa xử  lý xong'''
        # if no_quantities_done:
        #     view = self.env.ref('stock.view_immediate_transfer')
        #     wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
        #     return {
        #         'name': _('Immediate Transfer?'),
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'stock.immediate.transfer',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'res_id': wiz.id,
        #         'context': self.env.context,
        #     }
        #
        # if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
        #     view = self.env.ref('stock.view_overprocessed_transfer')
        #     wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'stock.overprocessed.transfer',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'res_id': wiz.id,
        #         'context': self.env.context,
        #     }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            new = self.env['stock.backorder.confirmation'].sudo().create({'pick_ids': [(6, 0, [self.id])]})
            new.process()
            return
        self.action_done()
        return

    @api.multi
    def validate_return_for_hotel_restaurant(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
                                 self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(
            float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(
                _('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(
                            _('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        '''chưa xử  lý xong'''
        # if no_quantities_done:
        #     view = self.env.ref('stock.view_immediate_transfer')
        #     wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
        #     return {
        #         'name': _('Immediate Transfer?'),
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'stock.immediate.transfer',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'res_id': wiz.id,
        #         'context': self.env.context,
        #     }
        #
        # if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
        #     view = self.env.ref('stock.view_overprocessed_transfer')
        #     wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'stock.overprocessed.transfer',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'res_id': wiz.id,
        #         'context': self.env.context,
        #     }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            new = self.env['stock.backorder.confirmation'].sudo().create({'pick_ids': [(6, 0, [self.id])]})
            new.process_cancel_backorder()
            return
        self.action_done()
        return

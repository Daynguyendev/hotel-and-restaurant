# from odoo import http, tools
# from odoo.http import request
# from datetime import datetime, timedelta
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
#
# MAP_INVOICE_TYPE_PARTNER_TYPE = {
#     'out_invoice': 'customer',
#     'out_refund': 'customer',
#     'in_invoice': 'supplier',
#     'in_refund': 'supplier',
# }
#
#
# class PrivateAPI(http.Controller):
#
#     @http.route("/kitchen/get-pos-info", type="json", auth="public", website=True)
#     def get_pos_info(self, pos_id):
#         pos = request.env["sea.pos.hotel.restaurant"].sudo().search([
#             ("id", "=", pos_id)
#         ], limit=1)
#         category_data = {}
#         if pos.limit_categories == True:
#             for category in pos.iface_available_categ_ids:
#                 category_data[category.id] = category.name
#         else:
#             categories = request.env["pos.category"].sudo().search([("company_id", "=", pos.company_id.id)])
#             for category in categories:
#                 category_data[category.id] = category.name
#         return {
#             "pos_name": pos.name,
#             "warehouse_id": pos.hotel_restaurant_branch_id.warehouse_id.id,
#             "customer_default_id": pos.customer_default_id.id,
#             "pos_categories": category_data,
#         }
#
#     @http.route("/kitchen/get-all-data", type="json", auth="user", website=True)
#     def get_order_data(self, **kw):
#         results = []
#         show_item_not_served = request.params["show_item_not_served"]
#         pos_id = request.params["pos_id"]
#         if show_item_not_served == True:
#             sale_orders = request.env["sale.order"].sudo().search([
#                 ("state", "=", "draft"),
#                 ("order_type", "=", "restaurant_order"),
#                 ("pos_hotel_restaurant_id", "=", pos_id)
#             ])
#
#             for order in sale_orders:
#                 data = {}
#                 data["name"] = order.name
#                 data["customer"] = order.partner_id.name
#                 data["status"] = order.state
#
#                 tables = []
#                 table_list = request.env["sea.restaurant.table"].sudo().search([("id", "in", order.table_list.ids)])
#                 for table in table_list:
#                     tables.append(table.name)
#                 if len(tables) == 0:
#                     tables.append("Bán mang về")
#                 data["tables"] = tables
#
#                 order_lines = []
#                 number_line = 0
#                 for line in order.order_line:
#                     if line.product_uom_qty == line.qty_reserved or line.product_id.type != "consu":
#                         continue
#                     line_data = {}
#                     line_data["product_name"] = line.product_id.name
#                     line_data["qty_order"] = line.product_uom_qty
#                     line_data["qty_done"] = line.qty_reserved
#                     line_data["note"] = line.remarks
#                     line_data["index"] = number_line
#                     number_line += 1
#
#                     order_lines.append(line_data)
#
#                 if len(order_lines) == 0:
#                     continue
#                 data["order_lines"] = order_lines
#                 results.append(data)
#
#         else:
#             # get sale orders by current date
#             request.env.cr.execute("""
#                     SELECT so.id, so.name, so.state, rp.name partner_name FROM sale_order so JOIN res_partner rp ON so.partner_id = rp.id
#                     WHERE so.order_type = 'restaurant_order' AND so.create_date::date = now()::date AND so.pos_hotel_restaurant_id = %s
#                 """ % (pos_id))
#             result_sale_order = list(request.env.cr.fetchall())
#             for order in result_sale_order:
#                 order_data = {}
#                 order_id = order[0]
#                 order_name = order[1]
#                 order_status = order[2]
#                 partner_name = order[3]
#
#                 order_data["name"] = order_name
#                 order_data["status"] = order_status
#                 order_data["customer"] = partner_name
#
#                 # get table list
#                 request.env.cr.execute("""
#                     select rt.name FROM sea_sale_order_table_rel sot JOIN sale_order so ON sot.sale_order_id = so.id
#                     JOIN sea_restaurant_table rt ON sot.table_id = rt.id WHERE so.id = %s
#                 """ % (order_id,))
#                 result_table_list = list(request.env.cr.fetchall())
#                 if len(result_table_list) == 0:
#                     tables = ["Bán mang về"]
#                 else:
#                     tables = []
#                     for table in result_table_list:
#                         table_name = table[0]
#                         tables.append(table_name)
#                 order_data["tables"] = tables
#
#                 # get sale order lines by order id
#                 order_lines = []
#                 request.env.cr.execute("""
#                     SELECT name, product_uom_qty, qty_reserved, remarks  FROM sale_order_line WHERE order_id = %s
#                 """ % (order_id,))
#                 result_sale_order_line = list(request.env.cr.fetchall())
#                 index = 0
#                 for order_line in result_sale_order_line:
#                     data_order_line = {}
#                     product_name = order_line[0]
#                     qty_order = order_line[1]
#                     qty_done = order_line[2]
#                     note = order_line[3]
#
#                     data_order_line["product_name"] = product_name
#                     data_order_line["qty_order"] = qty_order
#                     data_order_line["qty_done"] = qty_done
#                     data_order_line["note"] = note
#                     data_order_line["index"] = index
#                     order_lines.append(data_order_line)
#                     index += 1
#
#                 order_data["order_lines"] = order_lines
#                 results.append(order_data)
#         return results
#
#     @http.route("/room/get-room-available", type="json", auth="user", website=True)
#     def get_room_available(self, floor_id):
#         results = []
#         list_room = request.env["sea.hotel.room"].sudo().search([
#             ("company_id", "=", request.env.user.company_id.id),
#             ("available", "=", True),
#             ("floor_id", "=", int(floor_id))
#         ], order='id asc')
#
#         for room in list_room:
#             room_info = {
#                 "room_name": room.name,
#                 "room_capacity": room.capacity,
#                 "floor": room.floor_id.name,
#                 "room_type": room.room_type_id.name
#             }
#             results.append(room_info)
#         return results
#
#     @http.route("/room/get-room-occupied", type="json", auth="user", website=True)
#     def get_room_occupied(self, floor_id):
#         results = []
#         list_room = request.env["sea.hotel.room"].sudo().search([
#             ("company_id", "=", request.env.user.company_id.id),
#             ("available", "=", False),
#             ("floor_id", "=", int(floor_id))
#         ], order='id asc')
#
#         order_line_inprocess = request.env["sale.order.line"].sudo().search([
#             ("order_id.state", "!=", "done"),
#             ("order_id.order_type", "=", "hotel_order"),
#         ])
#         dict_order_line_inprocess = {}
#         for line in order_line_inprocess:
#             if line.room_id.id is not None:
#                 dict_order_line_inprocess[line.room_id.id] = line
#
#         for room in list_room:
#             room_info = {
#                 "room_name": room.name,
#                 "room_capacity": room.capacity,
#                 "floor": room.floor_id.name,
#                 "room_type": room.room_type_id.name
#             }
#             if room.id in dict_order_line_inprocess:
#                 order_line_data = dict_order_line_inprocess[room.id]
#                 room_info["check_in"] = (order_line_data.checkin_date + timedelta(hours=7)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#                 room_info["check_out"] = (order_line_data.checkout_date + timedelta(hours=7)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#                 room_info["customer"] = order_line_data.order_partner_id.name
#                 results.append(room_info)
#
#         return results
#
#     # @http.route("/kitchen/get-all-floor", type="json", auth="user", website=True)
#     # def get_all_floor(self, **kw):
#     #     results = {}
#     #     list_floor = request.env['sea.hotel.floor'].sudo().search([('company_id','=', request.env.user.company_id.id)])
#     #     for floor in list_floor:
#     #         results[floor.id] = floor.name
#     #
#     #     return results
#
#     @http.route("/table/get-all-table", type="json", auth="user", website=True)
#     def get_all_table(self, pos_id):
#         data = {}
#         draft_orders = request.env['sale.order'].sudo().search([
#             ('pos_hotel_restaurant_id', '=', pos_id),
#             ('order_type', '=', 'restaurant_order'),
#             ('state', '=', 'draft')
#         ])
#
#         tables = request.env['sea.restaurant.table'].sudo().search([('pos_hotel_restaurant_id', '=', pos_id)], order='name')
#         for table in tables:
#             table_info = {
#                 "table_id": table.id,
#                 "table_name": table.name,
#                 "capacity": table.capacity,
#                 "status": table.status,
#             }
#             for order in draft_orders:
#                 if table.id in order.table_list.ids:
#                     table_info["order_id"] = order.id
#                     table_info["order_no"] = order.name
#                     table_info["customer"] = order.partner_id.name
#                     table_info["order_date"] = (order.date_order + timedelta(hours=7)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#
#             if table.hotel_restaurant_area_id.name in data:
#                 data[table.hotel_restaurant_area_id.name].append(table_info)
#             else:
#                 data[table.hotel_restaurant_area_id.name] = [table_info]
#         results = []
#         for key in data:
#             results.append({"area": key, "list_table": data[key]})
#
#         return results
#
#     @http.route("/order/get-partner", type="json", auth="user", website=True)
#     def get_all_partner(self, company_id):
#         results = {}
#         list_partner = request.env['res.partner'].sudo().search([
#             ("company_id", "=", company_id),
#             ("active", "=", True),
#             ("customer", "=", True)
#         ])
#         for partner in list_partner:
#             results[partner.id] = partner.name
#
#         return results
#
#     @http.route("/order/get-all-product", type="json", auth="user", website=True)
#     def get_all_product(self, company_id):
#         results = {}
#         products = request.env['product.product'].sudo().search([("company_id", "=", company_id),("available_in_pos","=",True),("sale_ok","=",True)])
#         for product in products:
#             # print(product.id, product.name, product.lst_price, product.product_variant_ids, product.attribute_value_ids.name)
#             if product.attribute_value_ids:
#                 product_name = product.name + " (" + product.attribute_value_ids.name + ")"
#             else:
#                 product_name = product.name
#
#             results[product.id] = {
#                 "product_name": product_name,
#                 "price": product.lst_price,
#                 "uom": product.uom_id.name,
#                 "uom_id": product.uom_id.id,
#                 "pos_categ_id": product.pos_categ_id.id
#             }
#
#         return results
#
#     @http.route("/order/create-new-order", type="json", auth="user", website=True)
#     def create_new_order(self, **kw):
#         create_data = request.params
#         cr = request.env.cr
#         create_data["team_id"] = None
#         create_data["partner_id"] = int(request.params["partner_id"])
#         create_data["partner_invoice_id"] = create_data["partner_id"]
#         create_data["partner_shipping_id"] = create_data["partner_id"]
#         guest = request.env["res.partner"].browse(create_data["partner_id"])
#         create_data["pricelist_id"] = guest.property_product_pricelist.id
#         create_data["order_type"] = "restaurant_order"
#         response = request.env['sale.order'].sudo(int(request.params["user_id"])).create(create_data)
#         if response:
#             return {"code": 1, "status": "Done"}
#         return {"code": 0, "status": "Error"}
#
#     @http.route("/order/get-order-by-table", type="json", auth="user", website=True)
#     def get_order_by_table(self, **kw):
#         order_id = int(request.params["order_id"])
#         sale_order = request.env["sale.order"].browse(order_id)
#         sale_order_line = []
#         cr = request.env.cr
#         for order_line in sale_order.order_line:
#             if order_line.product_id.product_tmpl_id.type == 'product' or order_line.product_id.product_tmpl_id.type == 'consu':
#                 cr.execute("SELECT * FROM stock_route_product WHERE product_id = %s", (order_line.product_id.id,))
#                 result = cr.fetchall()
#                 if result:
#                     result_route_id = result[0]
#                 else:
#                     result_route_id = sale_order.pos_hotel_restaurant_id.default_route_id.id
#
#             sale_order_line.append({
#                 "product_id": order_line.product_id.id,
#                 "order_qty": order_line.product_uom_qty,
#                 "served_qty": order_line.qty_reserved,
#                 "order_line_id": order_line.id,
#                 "remarks": order_line.remarks,
#                 "route_id": result_route_id
#             })
#
#         response = {
#             "order_name": sale_order.name,
#             "guest_id": sale_order.partner_id.id,
#             "folio_id_restaurant": sale_order.folio_id_restaurant.id,
#             "date_order": (sale_order.date_order + timedelta(hours=7)).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
#             "list_table": [table.id for table in sale_order.table_list],
#             "order_lines": sale_order_line
#         }
#         return response
#
#     @http.route("/order/edit-order", type="json", auth="user", website=True)
#     def edit_order(self, **kw):
#         order_id = request.params["order_id"]
#         new_data = request.params
#         new_data.pop("order_id")
#         new_data["partner_id"] = int(request.params["partner_id"])
#         new_data["partner_invoice_id"] = new_data["partner_id"]
#         new_data["partner_shipping_id"] = new_data["partner_id"]
#         guest = request.env["res.partner"].browse(new_data["partner_id"])
#         new_data["pricelist_id"] = guest.property_product_pricelist.id
#         sale_order = request.env['sale.order'].browse(order_id)
#         response = sale_order.sudo(int(request.params["user_id"])).write(new_data)
#         if response:
#             return {"code": 1, "status": "Done"}
#         return {"code": 0, "status": "Error"}
#
#     @http.route("/invoice/get-invoice-by-id", type="json", auth="user", website=True)
#     def get_invoice_by_id(self, **kw):
#         invoice_id = request.params["invoice_id"]
#         invoice = request.env["account.invoice"].sudo().browse(invoice_id)
#         response = {
#             "invoice_number": invoice.number,
#             "amount_tax": invoice.amount_tax,
#             "amount_total": invoice.amount_total,
#             "amount_untaxed": invoice.amount_untaxed,
#             "total_discount": invoice.total_discount,
#             "remaining_due": invoice.residual,
#             "customer_name": invoice.partner_id.name,
#             "customer_id": invoice.partner_id.id,
#             "customer_type": MAP_INVOICE_TYPE_PARTNER_TYPE[invoice.type],
#             "communication": invoice.reference or invoice.name or invoice.number,
#             "currency_id": invoice.currency_id.id,
#             "currency_name": invoice.currency_id.name,
#             "payment_type": invoice.type in ('out_invoice', 'in_refund') and 'inbound' or 'outbound',
#         }
#         return response
#
#     @http.route("/invoice/get-journals-available", type="json", auth="user", website=True)
#     def get_journals_available(self, **kw):
#         branch_id = request.params["branch_id"]
#         journals = request.env["account.journal"].sudo().search([("hotel_restaurant_branch_id", "=", branch_id)])
#         response = {}
#         for journal in journals:
#             currency = journal.currency_id or journal.company_id.currency_id
#             name = "%s (%s)" % (journal.name, currency.name)
#             response[journal.id] = name
#         return response
#
#     @http.route("/payment/validate-payments", type="json", auth="user", website=True)
#     def validate_payments(self, **kw):
#         user_id = request.params["user_id"]
#         payments = request.params["payments"]
#         done = 0
#         for payment in payments:
#             payment["invoice_ids"] = [(6, 0, [payment["invoice_ids"]])]
#             new_payment = request.env['account.payment'].sudo(int(user_id)).create(payment)
#             new_payment.action_validate_invoice_payment()
#             done += 1
#         if done == len(payments):
#             return {"code": 1, "status": "Done"}
#         return {"code": 0, "status": "Error"}
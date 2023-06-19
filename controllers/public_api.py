# from odoo import http, tools
# from odoo.http import request
# from datetime import datetime, timedelta
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
#
#
# class PublicAPI(http.Controller):
#
#     @http.route("/order/create-sale-order", auth="public", website=False, csrf=False, type="json", methods=["POST"])
#     def create_sale_order(self, **kw):
#         create_data = request.params
#         create_data["team_id"] = None
#         create_data["partner_id"] = int(request.params["partner_id"])
#         create_data["partner_invoice_id"] = create_data["partner_id"]
#         create_data["partner_shipping_id"] = create_data["partner_id"]
#         guest = request.env["res.partner"].sudo(create_data["user_id"]).search([("id", "=", create_data["partner_id"])])
#         create_data["pricelist_id"] = guest.property_product_pricelist.id
#         create_data["order_type"] = "restaurant_order"
#         response = request.env['sale.order'].sudo(create_data["user_id"]).create(create_data)
#         if response:
#             return {"code": 1, "status": "Done"}
#         return {"code": 0, "status": "Error"}
#
#     @http.route("/order/edit-sale-order", auth="public", website=False, csrf=False, type="json", methods=["POST"])
#     def edit_sale_order(self, **kw):
#         order_id = request.params["order_id"]
#         new_data = request.params
#         new_data.pop("order_id")
#         new_data["partner_id"] = int(request.params["partner_id"])
#         new_data["partner_invoice_id"] = new_data["partner_id"]
#         new_data["partner_shipping_id"] = new_data["partner_id"]
#         guest = request.env["res.partner"].sudo(new_data["user_id"]).search([("id", "=", new_data["partner_id"])])
#         new_data["pricelist_id"] = guest.property_product_pricelist.id
#         sale_order = request.env['sale.order'].sudo(new_data["user_id"]).search([("id", "=", order_id)])
#         response = sale_order.sudo(new_data["user_id"]).write(new_data)
#         if response:
#             return {"code": 1, "status": "Done"}
#         return {"code": 0, "status": "Error"}
#
#     @http.route("/order/get-products", auth="public", website=False, csrf=False, type="json", methods=["POST"])
#     def get_products(self, **kw):
#         response = []
#         company_id = request.params["company_id"]
#         products = request.env["product.product"].sudo().search([
#             ("company_id", "=", company_id),
#             ("active", "=", True),
#             ("available_in_pos", "=", True)
#         ])
#         for product in products:
#             if product.attribute_value_ids:
#                 product_name = product.name + " (" + product.attribute_value_ids.name + ")"
#             else:
#                 product_name = product.name
#             response.append({
#                 "id": product.id,
#                 "name": product_name,
#                 "default_code": product.default_code,
#                 "list_price": product.lst_price,
#                 "uom_id": [product.uom_id.id, product.uom_id.name],
#                 "pos_categ_id": [product.pos_categ_id.id, product.pos_categ_id.name],
#                 "image_medium": product.image_medium,
#                 "available_in_pos": product.available_in_pos
#             })
#         return response
#
#     @http.route("/order/get-order-of-table", auth="public", website=False, csrf=False, type="json", methods=["POST"])
#     def get_order(self, **kw):
#         table_id = int(request.params["table_id"])
#         pos_id = int(request.params["pos_id"])
#         draft_orders = request.env['sale.order'].sudo().search([
#             ('pos_hotel_restaurant_id', '=', pos_id),
#             ('order_type', '=', 'restaurant_order'),
#             ('state', '=', 'draft')
#         ])
#
#         for order in draft_orders:
#             if table_id in order.table_list.ids:
#                 sale_order = order
#                 break
#
#         sale_order_line = []
#         for order_line in sale_order.order_line:
#             sale_order_line.append({
#                 "product_id": order_line.product_id.id,
#                 "order_qty": order_line.product_uom_qty,
#                 "served_qty": order_line.qty_reserved,
#                 "order_line_id": order_line.id,
#                 "remarks": order_line.remarks,
#             })
#         response = {
#             "order_id": sale_order.id,
#             "order_name": sale_order.name,
#             "guest_id": sale_order.partner_id.id,
#             "folio_id_restaurant": sale_order.folio_id_restaurant.id,
#             "date_order": (sale_order.date_order + timedelta(hours=7)).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
#             "list_table": [table.id for table in sale_order.table_list],
#             "order_lines": sale_order_line
#         }
#         return response

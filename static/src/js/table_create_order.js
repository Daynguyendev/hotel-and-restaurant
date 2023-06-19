//odoo.define("sea_hotel_restaurant.table_create_order", function(require) {
//    "use strict";
//
//    var AbstractAction = require("web.AbstractAction");
//    var core = require("web.core");
//    var QWeb = core.qweb;
//    var ajax = require("web.ajax");
//
//    var TableCreateOrder = AbstractAction.extend({
//        template: 'TableCreateOrderTemplate',
//
//        events: {
//            'click .table_available': 'open_view_create_order',
//            'click .table_occupied': 'open_view_edit_order',
//            'click .button-close-dialog': 'close_view_dialog',
//            'change #checkbox_is_hotel_guest': 'on_change_is_hotel_guest',
//            'click #button-search-guest': 'on_click_button_search_guest',
//            'keyup #search_box': 'on_search_partner',
//            'click .partners': 'on_click_partner',
//            'click #button_add_table': 'on_click_button_add_table',
//            'click .table_dropdown': 'on_click_table_dropdown',
//            'click .table_selected': 'on_click_table_selected',
//            'click .products': 'on_click_product_available',
//            'keyup .input-order-qty': 'on_change_order_qty',
//            'keyup .input-served-qty': 'on_change_served_qty',
//            'click .create-order-btn': 'on_click_create_order',
//            'click .edit-order-btn': 'on_click_confirm_change_order',
//            'keyup #search_product': 'on_search_product',
//            'click .product_search_match': 'on_click_product_available',
//            'dblclick .note-content': 'on_open_view_edit_note',
//            'click .btn-save-note': 'on_save_order_line_note',
//            'click .btn-unsave-note': 'on_close_view_edit_note',
//            'click .categories': 'on_click_category',
//            'click .remove-line': 'on_click_remove_line'
//        },
//
//        //**************************Note:
//        //When remove order_line: set product_id is false and get_data_render function only map line if product_id not false
//
//        init: function(parent, action) {
//            if (action.context.pos_id) {this.pos_id = action.context.active_id;}
//            else {this.pos_id = action.params.active_id;}
//
//            this.pos_name;
//            this.default_route_id;
//            this.pos_categories;
//            this.pos_customer_default;
//            this.category = -1;
//            this.company_id = action.context.company_ids[0];
//            this.user_id = action.context.uid;
//            this.order_id;
//            this.warehouse_id;
//            this.list_table = {};
//            this.list_table_area = [];
//            this.list_table_available = [];
//            this.selected_tables = [];
//            this.list_product = {};
//            this.list_product_selected = [];
//            this.list_partner = {};
//            this.guest_id;
//            this.is_hotel_guest = false;
//            this.folio_id_restaurant = false;
//            this.order_date_time;
//            this.div_search_guest_active = false;
//            this.div_search_table_active = false;
//            this.form_create_active = false;
//            this.form_edit_active = false;
//            var self = this;
//            this._super.apply(this, arguments);
//            self.get_pos_info();
//            self.get_table_list();
//            self.get_partner();
//            self.get_product();
//        },
//
//        get_data_render: function() {
//            var self = this;
//            var selected_tables = [];
//            var list_table_available = [];
//
//            for (var [table_id, table_data] of Object.entries(self.list_table)) {
//                if (self.selected_tables.includes(parseInt(table_id))) {
//                    selected_tables.push(table_data);
//                }
//                else if (self.list_table_available.includes(parseInt(table_id))) {
//                    list_table_available.push(table_data);
//                }
//            }
//
//            var selected_products = [];
//            for (var i = 0; i < self.list_product_selected.length; i++) {
//                var product_data = self.list_product_selected[i];
//                if (product_data["product_id"] != false) {
//                    product_data["product_name"] = self.list_product[product_data["product_id"]]["product_name"];
//                    var price_subtotal = self.list_product[product_data["product_id"]]["price"] * product_data["order_qty"];
//                    product_data["sub_total"] = Intl.NumberFormat().format(price_subtotal);
//                    selected_products.push(product_data);
//                }
//            };
//
//            var list_product = {};
//            for (var [product_id, product_data] of Object.entries(self.list_product)) {
//                if (self.category != -1) {
//                    if (product_data["pos_categ_id"] == self.category) {
//                        product_data["price_format"] = Intl.NumberFormat().format(product_data["price"]);
//                        list_product[product_id] = product_data;
//                    }
//                }
//                else {
//                    product_data["price_format"] = Intl.NumberFormat().format(product_data["price"]);
//                    list_product[product_id] = product_data;
//                }
//
//            }
//
//            var data_render = {
//                "pos_name": self.pos_name,
//                "pos_categories": self.pos_categories,
//                "category": self.category,
//                "form_create_active": self.form_create_active,
//                "form_edit_active": self.form_edit_active,
//                "table_datas": self.list_table_area,
//                "list_table_available": list_table_available,
//                "selected_tables": selected_tables,
//                "list_product": list_product,
//                "selected_products": selected_products,
//                "list_partner": self.list_partner,
//                "guest": self.guest_id ? self.list_partner[self.guest_id] : "",
//                "is_hotel_guest": self.is_hotel_guest,
//                "order_date_time": self.order_date_time == null ? "" : self.order_date_time,
//            };
//
//            return data_render;
//        },
//
//        get_pos_info: function() {
//            var self = this;
//            ajax.jsonRpc("/kitchen/get-pos-info", "call", {"pos_id": self.pos_id}).then(function (results) {
//                self.pos_name = results["pos_name"];
//                console.log(self.default_route_id)
//                console.log(self.warehouse_id) // In ra id của kho hàng tương ứng
//                self.warehouse_id = results["warehouse_id"];
//                results["pos_categories"]["-1"] = "All"
//                self.pos_categories = results["pos_categories"];
//                if (results["customer_default_id"] != false) {
//                    self.customer_default_id = parseInt(results["customer_default_id"]);
//                }
//            });
//        },
//
//        get_partner: function() {
//            var self = this;
//            ajax.jsonRpc("/order/get-partner", "call", {"company_id": self.company_id}).then(function (results) {
//                self.list_partner = results;
//                var data_render = self.get_data_render();
//                self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            });
//        },
//
//        get_product: function() {
//            var self = this;
//            ajax.jsonRpc("/order/get-all-product", "call", {"company_id": self.company_id}).then(function (results) {
//                self.list_product = results;
//                var data_render = self.get_data_render();
//                self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            });
//        },
//
//        get_table_list: function() {
//            var self = this;
//            ajax.jsonRpc("/table/get-all-table", "call", {"pos_id": self.pos_id}).then(function (results) {
//                  self.list_table_area = results;
//                  for (var i = 0; i < results.length; i++) {
//                        var tables = results[i]["list_table"];
//                        for (var j = 0; j < tables.length; j++) {
//                            var table = tables[j];
//                            if (table["status"] == "available") {
//                                self.list_table_available.push(parseInt(table["table_id"]))
//                            };
//                            self.list_table[table["table_id"]] = table;
//                        };
//                  };
//                  var data_render = self.get_data_render();
//                  self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            });
//        },
//
//        open_view_create_order: function(event) {
//
//            var table_id = event.currentTarget.dataset.table_id;
//            var self = this;
//            self.form_create_active = true;
//            var currentDateTime = new Date();
//            self.order_date_time = currentDateTime.getDate() + "/"
//            + (currentDateTime.getMonth() + 1) + "/" + currentDateTime.getFullYear() + " "
//            + currentDateTime.getHours() + ":" + currentDateTime.getMinutes() + ":" + currentDateTime.getSeconds();
//            self.selected_tables.push(parseInt(table_id));
//            self.guest_id = self.customer_default_id;
//            var data_render = self.get_data_render();
//            self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            document.getElementById("div-form-create").style.display = "block";
//        },
//
//        open_view_edit_order: function(event) {
//            var table_id = event.currentTarget.dataset.table_id;
//            var self = this;
//
//            for (var i = 0; i < self.list_table_area.length; i++) {
//                var list_table = self.list_table_area[i]["list_table"];
//                for (var j = 0; j < list_table.length; j++) {
//                    var table = list_table[j];
//                    if (table["table_id"] == table_id) {
//                        self.order_id = table["order_id"];
//                        j = list_table.length;
//                        i = self.list_table_area.length;
//                    }
//                }
//            }
//            ajax.jsonRpc("/order/get-order-by-table", "call", {"order_id": self.order_id}).then(function (results) {
//                  self.selected_tables = results["list_table"];
//                  self.list_product_selected = results["order_lines"];
//                  self.guest_id = results["guest_id"];
//                  self.default_route_id = results["route_id"];
//                  self.order_date_time = results["date_order"];
//                  self.form_edit_active = true;
//                  console.log('test results 123',self.default_route_id)
//                  if (results["folio_id_restaurant"] == false) {
//                        self.is_hotel_guest = false;
//                        self.folio_id_restaurant = false;
//                  }
//                  var data_render = self.get_data_render();
//                  self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//                  document.getElementById("div-form-edit").style.display = "block";
//            });
//
//        },
//
//        close_view_dialog: function(event) {
//            var self = this;
//            self.list_product_selected = [];
//            self.selected_tables = [];
//            self.order_id = null;
//            self.guest_id = null;
//            self.order_date_time = null;
//            self.div_search_guest_active = false;
//            self.div_search_table_active = false;
//            self.is_hotel_guest = false;
//            self.folio_id_restaurant = false;
//            self.category = -1;
//            if (self.form_create_active == true) {
//                self.form_create_active = false;
//                document.getElementById("div-form-create").style.display = "none";
//            }
//            if (self.form_edit_active == true) {
//                self.form_edit_active = false;
//                document.getElementById("div-form-edit").style.display = "none";
//            }
//        },
//
//        on_change_is_hotel_guest: function(event) {
//            var self = this;
//            self.is_hotel_guest = event.currentTarget.checked;
//            document.getElementById('div-folio').style.display = self.is_hotel_guest == true ? "block" : "none";
//        },
//
//        on_click_button_search_guest: function(event) {
//            this.div_search_guest_active = !this.div_search_guest_active;
//            document.getElementById('div-search-guest').style.display = this.div_search_guest_active == true ? "block" : "none";
//        },
//
//        on_search_partner: function(event) {
//            var self = this;
//            var search_key = document.getElementById('search_box').value;
//            var list_partner = document.getElementsByClassName('partners');
//            for (var i = 0; i < list_partner.length; i++) {
//                var button_text = list_partner[i].textContent || list_partner[i].innerText;
//                if (button_text.toUpperCase().includes(search_key.toUpperCase())) {
//                    list_partner[i].style.display = "block";
//                }
//                else {
//                    list_partner[i].style.display = "none";
//                }
//            };
//        },
//
//        on_click_partner: function(event) {
//            var self = this;
//            self.guest_id = event.currentTarget['name'];
//            self.div_search_guest_active = false;
//            var data_render = self.get_data_render();
//            self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            if (self.form_create_active == true) {
//                document.getElementById("div-form-create").style.display = "block";
//            }
//            else if (self.form_edit_active == true) {
//                document.getElementById("div-form-edit").style.display = "block";
//            }
//        },
//
//        on_click_button_add_table: function(event) {
//            this.div_search_table_active = !this.div_search_table_active;
//            document.getElementById('div-list-table-available').style.display = this.div_search_table_active == true ? "block" : "none";
//        },
//
//        on_click_table_dropdown: function(event) {
//            var self = this;
//            self.div_search_table_active = false;
//            var table_id = parseInt(event.currentTarget['name']);
//            self.selected_tables.push(table_id);
//            var data_render = self.get_data_render();
//            self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            if (self.form_create_active == true) {
//                document.getElementById("div-form-create").style.display = "block";
//            }
//            else if (self.form_edit_active == true) {
//                document.getElementById("div-form-edit").style.display = "block";
//            }
//        },
//
//        on_click_table_selected: function(event) {
//            var self = this;
//            var table_id = parseInt(event.currentTarget['name']);
//            self.selected_tables.splice(self.selected_tables.indexOf(table_id), 1);
//            var data_render = self.get_data_render();
//            self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            if (self.form_create_active == true) {
//                document.getElementById("div-form-create").style.display = "block";
//            }
//            else if (self.form_edit_active == true) {
//                document.getElementById("div-form-edit").style.display = "block";
//            }
//        },
//
//        on_click_product_available: function(event) {
//            var self = this;
//            var product_id = parseInt(event.currentTarget['name']);
//            self.list_product_selected.push({
//                "product_id": product_id,
//                "order_qty": 1,
//                "served_qty": 0,
//                "remarks": "",
//                "order_line_id": "virtual_" + (self.list_product_selected.length + 200),
//            });
//            var data_render = self.get_data_render();
//            self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            if (self.form_create_active == true) {
//                document.getElementById("div-form-create").style.display = "block";
//            }
//            else if (self.form_edit_active == true) {
//                document.getElementById("div-form-edit").style.display = "block";
//            }
//        },
//
//        on_change_order_qty: function(event) {
//            var self = this;
//            var document_id = event.currentTarget['id'];
//            var new_value = document.getElementById(document_id).value;
//            var id_change = event.currentTarget['name'];
//            for (var i = 0; i < self.list_product_selected.length; i++) {
//                var product = self.list_product_selected[i];
//                if (product['order_line_id'] == id_change) {
//                    self.list_product_selected[i]['order_qty'] = new_value == "" ? 0 : parseFloat(new_value);
//                    var price_subtotal = new_value == "" ? 0 : parseFloat(new_value) * self.list_product[product["product_id"]]["price"];
//                    document.getElementById("sub-total-" + id_change).innerHTML = Intl.NumberFormat().format(price_subtotal);
//                    break;
//                }
//            }
//        },
//
//        on_change_served_qty: function(event) {
//            var self = this;
//            var document_id = event.currentTarget['id'];
//            var new_value = document.getElementById(document_id).value;
//            var id_change = event.currentTarget['name'];
//            for (var i = 0; i < self.list_product_selected.length; i++) {
//                var product = self.list_product_selected[i];
//                if (product['order_line_id'] == id_change) {
//                    self.list_product_selected[i]['served_qty'] = new_value == "" ? 0 : parseFloat(new_value);
//                    break;
//                }
//            }
//        },
//
//        refresh_data: function() {
//            var self = this;
//            if (self.form_create_active == true) {
//                document.getElementById("div-form-create").style.display = "block";
//            }
//            else if (self.form_edit_active == true) {
//                document.getElementById("div-form-edit").style.display = "block";
//            }
//            self.list_product_selected = [];
//            self.list_table_available = [];
//            self.selected_tables = [];
//            self.order_id = null;
//            self.guest_id = null;
//            self.category = -1;
//            self.order_date_time = null;
//            self.div_search_guest_active = false;
//            self.div_search_table_active = false;
//            self.get_table_list();
//        },
//
//        on_click_create_order: function(event) {
//            var self = this;
//            var order_lines = [];
//            var [date, time] = self.order_date_time.split(" ");
//            var [day, month, year]  = date.split("/")
//            var [hours, minutes, seconds] = time.split(":");
//            var datetime = new Date(year, month - 1, day, hours, minutes, seconds, 0);
//            for (var i = 0; i < self.list_product_selected.length; i++) {
//                var product = self.list_product_selected[i];
//                if (product["order_line_id"].includes("virtual") && product["product_id"] != false) {
//                    var order_line_data = {
//                        "product_uom_qty": product["order_qty"] == "" ? 0 : product["order_qty"],
//                        "product_uom": self.list_product[product["product_id"]]["uom_id"],
//                        "qty_reserved": product["served_qty"] == "" ? 0 : product["served_qty"],
//                        "price_unit": self.list_product[product["product_id"]]["price"],
//                        "discount": 0,
//                        "remarks": product["remarks"],
//                        "product_id": product["product_id"],
//                    }
//                    order_lines.push([0, product["order_line_id"], order_line_data]);
//                }
//            }
//            console.log('test self',self.warehouse_id)
//
//            var params = {
//                "date_order": datetime,
//                "warehouse_id": self.warehouse_id,
//                "is_hotel_guest": self.is_hotel_guest,
//                "pos_hotel_restaurant_id": self.pos_id,
//                "folio_id_restaurant": self.folio_id_restaurant,
//                "partner_id": self.guest_id,
//                "table_list": [[6, false, self.selected_tables]],
//                "user_id": self.user_id,
//                "company_id": self.company_id,
//                "order_line": order_lines,
//                "table_id": self.selected_tables[0],
//            };
//
//            ajax.jsonRpc("/order/create-new-order", "call", params).then(function (results) {
//                  self.refresh_data();
//            });
//        },
//
//        on_click_confirm_change_order: function(event) {
//            var self = this;
//            var order_lines = [];
//            for (var i = 0; i < self.list_product_selected.length; i++) {
//                var product = self.list_product_selected[i];
//                if (product["order_line_id"].toString().includes("virtual")) {
//                    var order_line_data = {
//                        "product_uom_qty": product["order_qty"] == "" ? 0 : product["order_qty"],
//                        "product_uom": self.list_product[product["product_id"]]["uom_id"],
//                        "qty_reserved": product["served_qty"] == "" ? 0 : product["served_qty"],
//                        "price_unit": self.list_product[product["product_id"]]["price"],
//                        "discount": 0,
//                        "remarks": product["remarks"],
//                        "product_id": product["product_id"],
//                        "route_id": self.default_route_id,
//
//
//                    }
//                    order_lines.push([0, product["order_line_id"], order_line_data]);
//                }
//                else if (product["product_id"] != false) {
//                    var order_line_data = {
//                        "product_uom_qty": product["order_qty"] == "" ? 0 : product["order_qty"],
//                        "product_uom": self.list_product[product["product_id"]]["uom_id"],
//                        "qty_reserved": product["served_qty"] == "" ? 0 : product["served_qty"],
//                        "price_unit": self.list_product[product["product_id"]]["price"],
//                        "discount": 0,
//                        "remarks": product["remarks"],
//                        "product_id": product["product_id"]
//                    }
//                    order_lines.push([1, product["order_line_id"], order_line_data]);
//                }
//                else {
//                    order_lines.push([2, product["order_line_id"], false])
//                }
//            }
//
//            var params = {
//                "order_id": self.order_id,
//                "is_hotel_guest": self.is_hotel_guest,
//                "folio_id_restaurant": self.folio_id_restaurant,
//                "partner_id": self.guest_id,
//                "table_list": [[6, false, self.selected_tables]],
//                "user_id": self.user_id,
//                "order_line": order_lines
//            }
//
//            ajax.jsonRpc("/order/edit-order", "call", params).then(function (results) {
//                  self.refresh_data();
//            });
//        },
//
//        on_search_product: function(event) {
//            var self = this;
//            var search_key = document.getElementById('search_product').value;
//            var list_search_product = document.getElementsByClassName("product_search_match");
//            for (var i = 0; i < list_search_product.length; i++) {
//                var button_text = list_search_product[i].textContent || list_search_product[i].innerText;
//                if (button_text.toUpperCase().includes(search_key.toUpperCase()) && search_key != "") {
//                    list_search_product[i].style.display = "block";
//                }
//                else {
//                    list_search_product[i].style.display = "none";
//                }
//            };
//        },
//
//        on_open_view_edit_note: function(event) {
//            var self = this;
//            var content_note = "";
//            var order_line_id = event.currentTarget.dataset.order_line_id;
//            for (var i = 0; i < self.list_product_selected.length; i++) {
//                var product = self.list_product_selected[i];
//                if (product["order_line_id"] == order_line_id) {
//                    content_note = product["remarks"];
//                    break;
//                }
//            }
//            document.getElementById("content-note-" + order_line_id).value = content_note;
//            document.getElementById("div-content-note-" + order_line_id).style.display = "block";
//        },
//
//        on_save_order_line_note: function(event) {
//            var self = this;
//            var order_line_id = event.currentTarget['name'];
//            var content_note = document.getElementById("content-note-" + order_line_id).value;
//            for (var i = 0; i < self.list_product_selected.length; i++) {
//                var product = self.list_product_selected[i];
//                if (product["order_line_id"] == order_line_id) {
//                    product["remarks"] = content_note;
//                    break;
//                }
//            }
//            var data_render = self.get_data_render();
//            self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            if (self.form_create_active == true) {
//                document.getElementById("div-form-create").style.display = "block";
//            }
//            else if (self.form_edit_active == true) {
//                document.getElementById("div-form-edit").style.display = "block";
//            }
//        },
//
//        on_click_remove_line: function(event) {
//            var self = this;
//            var order_line_id = event.currentTarget.dataset.order_line_id;
//            for (var i = 0; i < self.list_product_selected.length; i++) {
//                var product = self.list_product_selected[i];
//                if (product['order_line_id'] == order_line_id) {
//                    self.list_product_selected[i]['product_id'] = false;
//                    break;
//                }
//            }
//
//            var data_render = self.get_data_render();
//            self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            if (self.form_create_active == true) {
//                document.getElementById("div-form-create").style.display = "block";
//            }
//            else if (self.form_edit_active == true) {
//                document.getElementById("div-form-edit").style.display = "block";
//            }
//        },
//
//        on_close_view_edit_note: function(event) {
//            var order_line_id = event.currentTarget['name'];
//            document.getElementById("div-content-note-" + order_line_id).style.display = "none";
//        },
//
//        on_click_category: function(event) {
//            var self = this;
//            var new_category = event.currentTarget['name'];
//            self.category = parseInt(new_category);
//
//            var data_render = self.get_data_render();
//            self.$el.html(QWeb.render("TableCreateOrderTemplate", data_render));
//            if (self.form_create_active == true) {
//                document.getElementById("div-form-create").style.display = "block";
//            }
//            else if (self.form_edit_active == true) {
//                document.getElementById("div-form-edit").style.display = "block";
//            }
//        }
//    });
//
//    core.action_registry.add("table_create_order_view_base", TableCreateOrder);
//    return TableCreateOrder;
//});
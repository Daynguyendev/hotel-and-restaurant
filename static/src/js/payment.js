//odoo.define("sea_hotel_restaurant.payment", function(require) {
//    "use strict";
//
//    var AbstractAction = require("web.AbstractAction");
//    var core = require("web.core");
//    var QWeb = core.qweb;
//    var ajax = require("web.ajax");
//
//    var PaymentView = AbstractAction.extend({
//        template: "PaymentTemplate",
//
//        events: {
//            'click .btn-journals': 'add_payment',
//            'keyup .input-tendered': 'change_tendered',
//            'click .validate-payment': 'validate_payment',
//        },
//
//        init: function(parent, action) {
//            this.user_id = action.context.uid;
//            if (action.context.invoice_id) {this.invoice_id = action.context.invoice_id;};
//            if (action.context.branch_id) {this.branch_id = action.context.branch_id;};
//            this.invoice_number = "";
//            this.amount_tax = "";
//            this.amount_total = "";
//            this.amount_untaxed = "";
//            this.remaining_due = "";
//            this.total_discount = "";
//            this.customer_name = "";
//            this.customer_id = "";
//            this.customer_type = "";
//            this.communication = "";
//            this.currency_id = "";
//            this.currency_name = "";
//            this.payment_type = "";
//            this.journals = {};
//            this.payments = {};
//            var self = this;
//            this._super.apply(this, arguments);
//            self.get_invoice();
//            self.get_journals_available();
//        },
//
//        get_data_render: function() {
//            var self = this;
//
//            var payments = {};
//            for (var [key, value] of Object.entries(self.payments)) {
//                payments[key] = {
//                    "due": Intl.NumberFormat().format(value["due"]),
//                    "tendered": value["tendered"] != "" ? Intl.NumberFormat().format(value["tendered"]) : "",
//                    "change": 0,
//                    "journal_id": self.journals[value["journal_id"]],
//                }
//            };
//
//            var data_render = {
//                "invoice_number": self.invoice_number,
//                "amount_tax": self.amount_tax != "" ? Intl.NumberFormat().format(self.amount_tax) : 0,
//                "amount_total": self.amount_total != "" ? Intl.NumberFormat().format(self.amount_total) : 0,
//                "amount_untaxed": self.amount_untaxed != "" ? Intl.NumberFormat().format(self.amount_untaxed) : 0,
//                "remaining_due": self.remaining_due != "" ? Intl.NumberFormat().format(self.remaining_due) : 0,
//                "total_discount": self.total_discount != "" ? Intl.NumberFormat().format(self.total_discount) : 0,
//                "customer": self.customer_name,
//                "journals": self.journals,
//                "payments": payments,
//            };
//
//            return data_render;
//        },
//
//        get_invoice: function() {
//            var self = this;
//            ajax.jsonRpc("/invoice/get-invoice-by-id", "call", {"invoice_id": self.invoice_id}).then(function (results) {
//                self.invoice_number = results["invoice_number"];
//                self.amount_tax = results["amount_tax"];
//                self.amount_total = results["amount_total"];
//                self.amount_untaxed = results["amount_untaxed"];
//                self.remaining_due = results["remaining_due"];
//                self.total_discount = results["total_discount"];
//                self.customer_name = results["customer_name"];
//                self.customer_id = results["customer_id"];
//                self.customer_type = results["customer_type"];
//                self.communication = results["communication"];
//                self.currency_id = results["currency_id"];
//                self.currency_name = results["currency_name"];
//                self.payment_type = results["payment_type"];
//                var data_render = self.get_data_render();
//                self.$el.html(QWeb.render("PaymentTemplate", data_render));
//            });
//        },
//
//        get_journals_available: function() {
//            var self = this;
//            ajax.jsonRpc("/invoice/get-journals-available", "call", {"branch_id": self.branch_id}).then(function (results) {
//                self.journals = results;
//                var data_render = self.get_data_render();
//                self.$el.html(QWeb.render("PaymentTemplate", data_render));
//            });
//        },
//
//        add_payment: function(event) {
//        var self = this;
//            if (self.remaining_due > 0) {
//                var journal_id = event.currentTarget.name;
//                var payment_data = {
//                    "due": self.remaining_due,
//                    "tendered": self.remaining_due,
//                    "change": "",
//                    "journal_id": journal_id,
//                };
//                var key = "payment_" + Object.keys(self.payments).length + 1;
//                self.payments[key] = payment_data;
//                self.remaining_due = 0;
//                var data_render = self.get_data_render();
//                self.$el.html(QWeb.render("PaymentTemplate", data_render));
//            }
//            else {
//                alert("Cannot add a new payment because the amount to be paid is already full");
//            }
//        },
//
//        change_tendered: function(event) {
//            var self = this;
//            var id_change = event.currentTarget.id;
//            var new_value = document.getElementById(id_change).value;
//            new_value = Number(new_value.replace(/[^\w\s]/gi,""));
//            var id_payment = event.currentTarget.name;
//            self.payments[id_payment]["tendered"] = new_value;
//            document.getElementById(id_change).value = new_value != "" ? Intl.NumberFormat().format(new_value) : "";
//            if (new_value - self.payments[id_payment]["due"] > 0) {
//                self.payments[id_payment]["change"] = new_value - self.payments[id_payment]["due"];
//                document.getElementById("change-" + id_payment).innerHTML = Intl.NumberFormat().format(self.payments[id_payment]["change"]);
//            }
//            else {
//                document.getElementById("change-" + id_payment).innerHTML = 0;
//            }
//            self.remaining_due = self.payments[id_payment]["due"] - new_value;
//            if (self.remaining_due < 0) {
//                document.getElementById("amount_due").style.color = "red";
//            }
//            document.getElementById("amount_due").innerHTML = Intl.NumberFormat().format(self.remaining_due);
//        },
//
//        validate_payment: function(event) {
//            var self = this;
//            var now = new Date();
//            var payment_date = now.getFullYear() + "-" + (now.getMonth() + 1) + "-" + now.getDate();
//            var payments = [];
//            var data_payment;
//            for (var [key, value] of Object.entries(self.payments)) {
//                data_payment = {
//                    "payment_type": self.payment_type,
//                    "partner_type": self.customer_type,
//                    "partner_id": self.customer_id,
//                    "amount": value["due"],
//                    "currency_id": self.currency_id,
//                    "payment_date": payment_date,
//                    "communication": self.communication,
//                    "payment_difference_handling": "open",
//                    "writeoff_label": "Write-Off",
//                    "journal_id": value["journal_id"],
//                    "payment_method_id": 1,
//                    "payment_token_id": false,
//                    "partner_bank_account_id": false,
//                    "writeoff_account_id": false,
//                    "invoice_ids": self.invoice_id,
//                }
//                payments.push(data_payment)
//            }
//            ajax.jsonRpc("/payment/validate-payments", "call", {"payments": payments, "user_id": self.user_id}).then(function (results) {
//                if (results["code"] == 1) {
//                    self.do_action({
//                        'type': 'ir.actions.act_window_close',
//                    });
//                }
//                else {
//                    alert("An error occurred during payment. Please contact the developer!");
//                }
//            });
//        },
//    });
//
//    core.action_registry.add("payment_view", PaymentView);
//    return PaymentView;
//});
//odoo.define("sea_hotel_restaurant.kitchen", function(require) {
//    "use strict";
//
//    var AbstractAction = require("web.AbstractAction");
//    var core = require("web.core");
//    var QWeb = core.qweb;
//    var ajax = require("web.ajax");
//
//    var SECOND_RELOAD = 30000; // 30s
//
//    var KitchenBase = AbstractAction.extend({
//        template: 'KitchenTemplate',
//
//        events: {
//            'change #show_item_not_served': 'on_change_checkbox'
//        },
//
//        init: function(parent, action) {
//            if (action.context.pos_id) {
//                this.pos_id = action.context.active_id;
//            }
//            else {
//                this.pos_id = action.params.active_id;
//            }
//
//            this.show_item_not_served = true;
//            this.pos_name = "";
//            var self = this;
//            this._super.apply(this, arguments);
//            self.get_pos_info();
//            self.get_order_data();
//        },
//
//        on_change_checkbox: function(event) {
//            var self = this;
//            clearTimeout(this.timer);
//            this.show_item_not_served = event.currentTarget.checked;
//            self.get_order_data();
//        },
//
//        get_pos_info: function() {
//            var self = this;
//            ajax.jsonRpc("/kitchen/get-pos-info", "call", {"pos_id": self.pos_id}).then(function (results) {
//                self.pos_name = results["pos_name"];
//            });
//        },
//
//        get_order_data: function() {
//            var self = this;
//            ajax.jsonRpc("/kitchen/get-all-data", "call", {"show_item_not_served": self.show_item_not_served, "pos_id": self.pos_id}).then(function (results){
//                var data_render = {
//                    "show_item_not_served": self.show_item_not_served,
//                    "pos_name": self.pos_name,
//                };
//                if (results.length != 0) {
//                    data_render["order_lines"] = results
//                }
//                self.$el.html(QWeb.render("KitchenTemplate", data_render));
//            });
//            clearTimeout(this.timer);
//            this.timer = setTimeout(function() {self.get_order_data()}, SECOND_RELOAD);
//        },
//
//        destroy: function () {
//            this._super.apply(this, arguments);
//            clearTimeout(this.timer);
//        },
//    });
//
//    core.action_registry.add("kitchen_view_base", KitchenBase);
//    return KitchenBase;
//});
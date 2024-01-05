odoo.define('account_plus.reconciliation', function (require) {
    "use strict";

    var core = require('web.core');
    var reconcile = require('account.reconciliation');

    var QWeb = core.qweb;
    var _t = core._t;

    reconcile.manualReconciliationLine.include({
        balanceChanged: function () {
            var self = this;
            var balance = self.get("balance");

            /// Start - Added by Odootech --------------------------------------------
            var lines_created = self.get("lines_created").length + (self.islineCreatedBeingEditedValid() ? 1 : 0);
            /// End - Added by Odootech ----------------------------------------------

            self.$(".button_reconcile").removeClass("btn-primary");
            self.$(".button_reconcile").text(_t("Reconcile"));
            self.persist_action = "reconcile";
            /// Start - Edited by Odootech -------------------------------------------
            if (self.get("mv_lines_selected").length + lines_created < 2) {
                /// End - Edited by Odootech ---------------------------------------------
                self.$(".button_reconcile").text(_t("Skip"));
                self.persist_action = "mark_as_reconciled";
            } else if (self.monetaryIsZero(balance)) {
                self.$(".button_reconcile").addClass("btn-primary");
            }

            self.$(".tbody_open_balance").empty();
            /// Start - Edited by Odootech -------------------------------------------
            if ((!self.monetaryIsZero(balance)) && self.get("mv_lines_selected").length > 0) {
                /// End - Edited by Odootech ---------------------------------------------
                var debit = (balance > 0 ? self.formatCurrencies(balance, self.get("currency_id")) : "");
                var credit = (balance < 0 ? self.formatCurrencies(-1 * balance, self.get("currency_id")) : "");
                var $line = $(QWeb.render("manual_reconciliation_line_open_balance", {
                    debit: debit,
                    credit: credit,
                    label: _t("Create writeoff")
                }));
                self.$(".tbody_open_balance").append($line);
            }
        },
    });

});
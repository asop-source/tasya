# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sh_stock_barcode_mobile = fields.Char(string="Mobile Barcode")
    sh_stock_bm_is_cont_scan = fields.Char(
        string='Continuously Scan?', default=lambda self: self.env.company.sh_stock_bm_is_cont_scan, readonly=True)

    @api.onchange('sh_stock_barcode_mobile')
    def _onchange_sh_stock_barcode_mobile(self):
        if not self.sh_stock_barcode_mobile:
            return

        def sh_send_bus(company, title, message, notify_type):
            send_bus = False
            play_sound = False
            if company and notify_type:
                send_bus = bool((company.sh_stock_bm_is_notify_on_success and notify_type ==
                                'success') or company.sh_stock_bm_is_notify_on_fail)
                play_sound = bool(send_bus and (
                    (notify_type == 'success' and company.sh_stock_bm_is_sound_on_success) or company.sh_stock_bm_is_sound_on_fail))
            if send_bus:
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'sound_notification', {
                                             'title': _(title), 'message': message, 'type': notify_type, 'play_sound': play_sound})

        barcode = self.sh_stock_barcode_mobile
        company_sudo = (self.company_id or self.env.company).sudo()

        if not self.picking_type_id:
            message = _('You must first select a Operation Type.')
            sh_send_bus(company_sudo, "Failed", message, "danger")
            return

        if self and self.state not in ['assigned', 'draft', 'confirmed']:
            selections = self.fields_get()['state']['selection']
            value = next((v[1] for v in selections if v[0]
                         == self.state), self.state)

            message = _("You can not scan item in %s state.") % (value)
            sh_send_bus(company_sudo, "Failed", message, "danger")
            return

        stock_moves = False
        domain = []
        if company_sudo.sh_stock_barcode_mobile_type == 'barcode':
            stock_moves = self.move_ids_without_package.filtered(
                lambda ml: ml.product_id.barcode == barcode)
            domain = [("barcode", "=", barcode)]

        elif company_sudo.sh_stock_barcode_mobile_type == 'int_ref':
            stock_moves = self.move_ids_without_package.filtered(
                lambda ml: ml.product_id.default_code == barcode)
            domain = [("default_code", "=", barcode)]

        elif company_sudo.sh_stock_barcode_mobile_type == 'sh_qr_code':
            stock_moves = self.move_ids_without_package.filtered(
                lambda ml: ml.product_id.sh_qr_code == barcode)
            domain = [("sh_qr_code", "=", barcode)]

        elif company_sudo.sh_stock_barcode_mobile_type == 'all':
            stock_moves = self.move_ids_without_package.filtered(lambda ml: barcode in (ml.product_id.barcode,
                                                                                       ml.product_id.default_code,
                                                                                       ml.product_id.sh_qr_code))
            domain = ["|", "|", ("default_code", "=", barcode),
                      ("barcode", "=", barcode),
                      ("sh_qr_code", "=", barcode)]

        if stock_moves:
            move = stock_moves[:1]
            if self.state == 'draft' and move.is_initial_demand_editable:
                move.product_uom_qty = move.product_uom_qty + 1
                message = _(
                    'Product: %s<br /> Qty: %s') % (move.product_id.name, move.product_uom_qty)
                sh_send_bus(company_sudo, "Succeed",
                            message, "success")

            elif move.show_details_visible:
                message = _(
                    "You can not scan product item for Detailed Operations directly here, Pls click detail button (at end each line) and than rescan your product item.")
                sh_send_bus(company_sudo, "Failed", message, "danger")

            elif move.is_quantity_done_editable:
                move.quantity = move.quantity + 1
                message = _(
                    'Product: %s<br /> Qty: %s') % (move.product_id.name, move.quantity)
                sh_send_bus(company_sudo, "Succeed",
                            message, "success")

                if move.quantity == move.product_uom_qty + 1:
                    message = _(
                        'Be Careful! Quantity exceed than initial demand!')
                    sh_send_bus(company_sudo, "Alert",
                                message, "warning")

        elif self.state == 'draft':
            if company_sudo.sh_stock_bm_is_add_product:
                search_product = self.env["product.product"].search(
                    domain, limit=1)
                if search_product:
                    order_line_val = {"name": search_product.name,
                                      "product_id": search_product.id,
                                      "price_unit": search_product.lst_price,
                                      "location_id": self.location_id.id,
                                      "product_uom_qty": 1,
                                      "location_dest_id": self.location_dest_id.id, }
                    if search_product.uom_id:
                        order_line_val.update(
                            {"product_uom": search_product.uom_id.id, })

                    new_order_line = self.move_ids_without_package.new(
                        order_line_val)

                    new_order_line._onchange_product_id()
                    self.move_ids_without_package += new_order_line
                    message = _(
                        'Product: %s<br /> Qty: %s') % (search_product.name, 1)
                    sh_send_bus(company_sudo, "Succeed",
                                message, "success")
                else:
                    message = _(
                        "Scanned Internal Reference/Barcode/QR Code '%s' does not exist in any product!") % (barcode)
                    sh_send_bus(company_sudo, "Failed",
                                message, "danger")
            else:
                message = _(
                    "Scanned Internal Reference/Barcode/QR Code '%s' does not exist in any product!") % (barcode)
                sh_send_bus(company_sudo, "Failed", message, "danger")
        else:
            message = _(
                "Scanned Internal Reference/Barcode/QR Code '%s' does not exist in any product!") % (barcode)
            sh_send_bus(company_sudo, "Failed",
                        message, "danger")

# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.


from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError


class StockAdjustment(http.Controller):

    @http.route(['/sh_inventory_adjustment_barcode_mobile/get_widget_data'], type="json", auth="user", cors="*")
    def sh_barcode_mobile_get_widget_data(self, **post):
        values = {}
        user_is_stock_manager = request.env.user.has_group(
            'stock.group_stock_manager')
        user_has_stock_multi_locations = request.env.user.has_group(
            'stock.group_stock_multi_locations')
        values['user_is_stock_manager'] = user_is_stock_manager
        values['user_has_stock_multi_locations'] = user_has_stock_multi_locations
        values['sh_inventory_adjt_bm_is_cont_scan'] = request.env.company.sudo(
        ).sh_inventory_adjt_bm_is_cont_scan
        if user_has_stock_multi_locations:
            domain = [('usage', 'in', ['internal', 'transit'])]
            locations = request.env['stock.location'].search_read(
                domain, ['id', 'display_name'])
            values['locations'] = locations
        return values

    @http.route(['/sh_all_in_one_mbs/sh_barcode_scanner_search_stock_quant_by_barcode'], type="json", auth="user", cors="*")
    def sh_barcode_scanner_search_stock_quant_by_barcode(self, domain=None, barcode=None, location_id=None, location_name=None, scan_negative_stock=None, **post):

        company_sudo = request.env.company.sudo()
        play_on_success = company_sudo.sh_inventory_adjt_bm_is_sound_on_success
        play_on_fail = company_sudo.sh_inventory_adjt_bm_is_sound_on_fail

        is_qty_updated = False

        if barcode:
            domain_product = []
            if company_sudo.sh_inventory_adjt_barcode_mobile_type == "barcode":
                domain_product = [("product_id.barcode", "=", barcode)]
            elif company_sudo.sh_inventory_adjt_barcode_mobile_type == "int_ref":
                domain_product = [("product_id.default_code", "=", barcode)]
            elif company_sudo.sh_inventory_adjt_barcode_mobile_type == "sh_qr_code":
                domain_product = [("product_id.sh_qr_code", "=", barcode)]
            elif company_sudo.sh_inventory_adjt_barcode_mobile_type == "all":
                domain_product = ["|", "|", ("product_id.default_code", "=", barcode), (
                    "product_id.barcode", "=", barcode), ("product_id.sh_qr_code", "=", barcode)]

            if not domain:
                domain = [('location_id.usage', 'in', ['internal', 'transit'])]

            if location_id:
                domain.append(('location_id', '=', location_id))

            domain = domain + domain_product
            quant = request.env['stock.quant'].search(domain)
            if quant:
               # Take only one first quant if multiple quants found.
                is_qty_updated = True
                quant = quant[0]
                if scan_negative_stock:
                    quant.inventory_quantity -= 1
                else:
                    quant.inventory_quantity += 1
                message = _("Product Added Successfully")
                # -----------------------------
                # Give Success Message
                if company_sudo.sh_inventory_adjt_bm_is_notify_on_success:
                    message = _('Product: %s <br /> Counted Quantity: %s') % (
                        quant.product_id.name, quant.inventory_quantity)
                    request.env['bus.bus']._sendone(request.env.user.partner_id, 'sound_notification', {'title': _(
                        'Succeed'), 'message': message, 'type': 'success', 'play_sound': play_on_success})
                # -----------------------------
                # Give Success Message

            else:
                is_qty_updated = False
                message = _(
                    'Record not found for this scanned barcode: ' + barcode)
                if location_name:
                    message = _('Record not found for this scanned barcode: ' +
                                barcode + ' <br /> Location: ' + location_name)

                # -----------------------------
                # Give Failer Message
                if company_sudo.sh_inventory_adjt_bm_is_notify_on_fail:
                    request.env['bus.bus']._sendone(request.env.user.partner_id, 'sound_notification', {
                                                    'title': _('Failed'), 'message': message, 'type': 'danger', 'play_sound': play_on_fail})

                # -----------------------------
                # Give Failer Message

        else:
            is_qty_updated = False
            message = _(
                'Please enter/type barcode in barcode input and try again.')

            # -----------------------------
            # Give Failer Message
            if company_sudo.sh_inventory_adjt_bm_is_notify_on_fail:
                request.env['bus.bus']._sendone(request.env.user.partner_id, 'sound_notification', {
                                                'title': _('Failed'), 'message': message, 'type': 'danger', 'play_sound': play_on_fail})
            # -----------------------------
            # Give Failer Message

        return {"is_qty_updated": is_qty_updated, "message": message}

    @http.route(['/sh_all_in_one_mbs/sh_barcode_scanner_stock_quant_tree_btn_apply'], type="json", auth="user", cors="*")
    def sh_barcode_scanner_stock_quant_tree_btn_apply(self, domain=None, **post):
        if not request.env.user.has_group('stock.group_stock_manager'):
            raise UserError(_('Only stock manager can do this action'))

        message = ""
        is_qty_applied = False

        if not domain:
            domain = [('location_id.usage', 'in', ['internal', 'transit'])]
        quants = request.env['stock.quant'].search(
            domain+[('inventory_quantity_set', '!=', False),])
        if quants:
            for quant in quants:
                quant.action_apply_inventory()
            is_qty_applied = True
            message = 'All Counted Quantity successfully applied'
        else:
            is_qty_applied = False
            message = 'No any inventory line found for this action - Apply'
        return {"is_qty_applied": is_qty_applied, "message": message}

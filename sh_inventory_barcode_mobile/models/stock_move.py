# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    sh_stock_move_barcode_mobile = fields.Char(string="Mobile Barcode")
    sh_stock_move_bm_is_cont_scan = fields.Char(
        string='Continuously Scan?', default=lambda self: self.env.company.sh_stock_bm_is_cont_scan, readonly=True)

    def sh_send_bus(self, company, title, message, notify_type):
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

    def sh_stock_move_barcode_mobile_has_tracking(self, company_sudo, barcode):
        if self.picking_code == 'incoming':
            # FOR PURCHASE
            # LOT PRODUCT
            if self.product_id.tracking == 'lot':
                # First Time Scan
                lines = self.move_line_ids.filtered(
                    lambda r: not r.lot_name)
                if lines:
                    line = lines[:1]

                    quantity = line.quantity + 1
                    vals_line = {'quantity': quantity,
                                 'lot_name': barcode, }
                    self.update({'move_line_ids': [
                                (1, line.id, vals_line)]})

                    # success message here
                    message = _('Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (
                        self.product_id.name, line.quantity, barcode)
                    self.sh_send_bus(company_sudo, "Succeed",
                                     message, 'success')

                else:
                    # Second Time Scan
                    lines = self.move_line_ids.filtered(
                        lambda r: r.lot_name == barcode)
                    if lines:
                        line = lines[:1]

                        quantity = line.quantity + 1
                        vals_line = {'quantity': quantity, }
                        self.update({'move_line_ids': [
                                    (1, line.id, vals_line)]})

                        # success message here
                        message = _('Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (
                            self.product_id.name, line.quantity, barcode)
                        self.sh_send_bus(
                            company_sudo, "Succeed", message, 'success')

                    else:
                        # New Barcode Scan then create new line
                        vals_line = {'product_id': self.product_id.id,
                                     'location_dest_id': self.location_dest_id.id,
                                     'lot_name': barcode,
                                     'quantity': 1,
                                     'product_uom_id': self.product_uom.id,
                                     'location_id': self.location_id.id, }
                        self.update(
                            {'move_line_ids': [(0, 0, vals_line)]})

                        # success message here
                        message = _(
                            'Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (self.product_id.name, 1, barcode)
                        self.sh_send_bus(
                            company_sudo, "Succeed", message, 'success')

            # SERIAL PRODUCT
            if self.product_id.tracking == 'serial':
                # VALIDATION SERIAL NO. ALREADY EXIST.
                lines = self.move_line_ids.filtered(
                    lambda r: r.lot_name == barcode)
                if lines:
                    # failed message here
                    message = _('Serial Number already exist!')
                    self.sh_send_bus(company_sudo, "Failed", message, 'danger')
                    return

                # First Time Scan
                lines = self.move_line_ids.filtered(
                    lambda r: not r.lot_name)
                if lines:
                    line = lines[:1]

                    quantity = line.quantity + 1
                    vals_line = {'quantity': quantity, 'lot_name': barcode}
                    self.update({'move_line_ids': [
                                (1, line.id, vals_line)]})

                    # success message here
                    message = _('Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (
                        self.product_id.name, line.quantity, barcode)
                    self.sh_send_bus(company_sudo, "Succeed",
                                     message, 'success')

                else:
                    # Create new line if not found any unallocated serial number line
                    vals_line = {'product_id': self.product_id.id,
                                 'location_dest_id': self.location_dest_id.id,
                                 'lot_name': barcode,
                                 'quantity': 1,
                                 'product_uom_id': self.product_uom.id,
                                 'location_id': self.location_id.id, }
                    self.update(
                        {'move_line_ids': [(0, 0, vals_line)]})

                    # success message here
                    message = _(
                        'Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (self.product_id.name, 1, barcode)
                    self.sh_send_bus(company_sudo, "Succeed",
                                     message, 'success')

            quantity_done = 0
            for move_line in self.move_line_ids:
                quantity_done += move_line.product_uom_id._compute_quantity(
                    move_line.quantity, self.product_uom, round=False)

            if quantity_done == self.product_uom_qty + 1:
                # failed message here
                message = _('Be Careful! Quantity exceed than initial demand!')
                self.sh_send_bus(company_sudo, "Alert", message, 'warning')
                return

        elif self and self.picking_code in ['outgoing', 'internal']:
            # FOR SALE
            # LOT PRODUCT
            quant_obj = self.env['stock.quant']

            # FOR LOT PRODUCT
            if self.product_id.tracking == 'lot':
                # First Time Scan
                quant = quant_obj.search([('product_id', '=', self.product_id.id),
                                          ('quantity', '>', 0),
                                          ('location_id.usage', '=', 'internal'),
                                          ('lot_id.name', '=', barcode),
                                          ('location_id', 'child_of', self.location_id.id)], limit=1)

                if not quant:
                    # failed message here
                    message = _(
                        'There are no available qty for this lot: %s') % (barcode)
                    self.sh_send_bus(company_sudo, "Failed", message, 'danger')
                    return

                lines = self.move_line_ids.filtered(lambda r: not r.lot_id)
                if lines:
                    line = lines[:1]
                    quantity = line.quantity + 1
                    vals_line = {'quantity': quantity,
                                 'lot_id': quant.lot_id.id}
                    self.update({'move_line_ids': [(1, line.id, vals_line)]})

                    # success message here

                    message = _('Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (
                        self.product_id.name, line.quantity, quant.lot_id.name)
                    self.sh_send_bus(company_sudo, "Succeed",
                                     message, 'success')

                else:
                    # Second Time Scan
                    lines = self.move_line_ids.filtered(
                        lambda r: r.lot_id.name == barcode)
                    if lines:
                        line = lines[:1]
                        quantity = line.quantity + 1
                        vals_line = {'quantity': quantity}
                        self.update(
                            {'move_line_ids': [(1, line.id, vals_line)]})
                        # success message here
                        message = _('Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (
                            self.product_id.name, line.quantity, quant.lot_id.name)
                        self.sh_send_bus(
                            company_sudo, "Succeed", message, 'success')

                    else:
                        # New Barcode Scan then create new line
                        vals_line = {'product_id': self.product_id.id,
                                     'location_dest_id': self.location_dest_id.id,
                                     'lot_id': quant.lot_id.id,
                                     'quantity': 1,
                                     'product_uom_id': self.product_uom.id,
                                     'location_id': quant.location_id.id, }
                        self.update({'move_line_ids': [(0, 0, vals_line)]})
                        # success message here
                        message = _('Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (
                            self.product_id.name, 1, quant.lot_id.name)
                        self.sh_send_bus(
                            company_sudo, "Succeed", message, 'success')

            # FOR SERIAL PRODUCT
            if self.product_id.tracking == 'serial':
                # First Time Scan
                lines = self.move_line_ids.filtered(
                    lambda r: r.lot_id.name == barcode)
                if lines:
                    line = lines[:1]

                    quantity = line.quantity + 1
                    if float_compare(quantity, 1.0, precision_rounding=line.product_id.uom_id.rounding) != 0:
                        message = _(
                            'You can only process 1.0 %s of products with unique serial number.') % line.product_id.uom_id.name
                        self.sh_send_bus(
                            company_sudo, "Failed", message, 'danger')
                    else:
                        vals_line = {'quantity': quantity, }
                        self.update({'move_line_ids': [(1, line.id, vals_line)]})

                        # success message here
                        message = _('Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (
                            self.product_id.name, line.quantity, barcode)
                        self.sh_send_bus(company_sudo, "Succeed",
                                        message, 'success')


                else:
                    list_allocated_serial_ids = [
                        line.lot_id.id for line in self.move_line_ids if line.lot_id]

                    # if need new line.
                    quant = quant_obj.search([('product_id', '=', self.product_id.id),
                                              ('quantity', '>', 0),
                                              ('location_id.usage',
                                               '=', 'internal'),
                                              ('lot_id.name', '=', barcode),
                                              ('location_id', 'child_of',
                                               self.location_id.id),
                                              ('lot_id.id', 'not in', list_allocated_serial_ids)], limit=1)

                    if not quant:
                        # failed message here
                        message = _(
                            'There are no available qty for this lot/serial: %s') % (barcode)
                        self.sh_send_bus(
                            company_sudo, "Failed", message, 'danger')
                        return

                    # New Barcode Scan then create new line
                    vals_line = {'product_id': self.product_id.id,
                                 'location_dest_id': self.location_dest_id.id,
                                 'lot_id': quant.lot_id.id,
                                 'quantity': 1,
                                 'product_uom_id': self.product_uom.id,
                                 'location_id': quant.location_id.id, }
                    self.update({'move_line_ids': [(0, 0, vals_line)]})

                    # success message here
                    message = _('Product: %s<br /> Qty: %s<br /> lot/serial: %s') % (
                        self.product_id.name, 1, quant.lot_id.name)
                    self.sh_send_bus(company_sudo, "Succeed",
                                     message, 'success')

            quantity_done = 0
            for move_line in self.move_line_ids:
                quantity_done += move_line.product_uom_id._compute_quantity(
                    move_line.quantity, self.product_uom, round=False)

            if self.picking_code == 'outgoing' and quantity_done == self.product_uom_qty + 1:
                # failed message here
                message = _('Be Careful! Quantity exceed than initial demand!')
                self.sh_send_bus(company_sudo, "Alert", message, 'warning')
                return
        else:
            # failed message here
            message = _(
                'Picking type is not outgoing or incoming or internal transfer.')
            self.sh_send_bus(company_sudo, "Failed", message, 'danger')

    def sh_stock_move_barcode_mobile_no_tracking(self, company_sudo, barcode):
        move_lines = self.move_line_ids
        if not move_lines:
            message = _('Pls add all product items in line than rescan.')
            self.sh_send_bus(company_sudo, "Failed", message, 'danger')
        else:
            similar_lines = False
            if company_sudo.sh_stock_barcode_mobile_type == 'barcode':
                if self.product_id.barcode == barcode:
                    similar_lines = move_lines.filtered(
                        lambda ml: ml.product_id.barcode == barcode)

            elif company_sudo.sh_stock_barcode_mobile_type == 'int_ref':
                if self.product_id.default_code == barcode:
                    similar_lines = move_lines.filtered(
                        lambda ml: ml.product_id.default_code == barcode)

            elif company_sudo.sh_stock_barcode_mobile_type == 'sh_qr_code':
                if self.product_id.sh_qr_code == barcode:
                    similar_lines = move_lines.filtered(
                        lambda ml: ml.product_id.sh_qr_code == barcode)
            elif company_sudo.sh_stock_barcode_mobile_type == 'all':
                if barcode in (self.product_id.barcode, self.product_id.default_code, self.product_id.sh_qr_code):
                    similar_lines = move_lines.filtered(lambda ml: barcode in (
                        ml.product_id.barcode, ml.product_id.default_code, ml.product_id.sh_qr_code))

            if not bool(similar_lines):
                message = _(
                    'Scanned Internal Reference/Barcode not exist in any product!')
                self.sh_send_bus(company_sudo, "Failed", message, 'danger')
            else:
                quantity = similar_lines[-1].quantity + 1
                if self.picking_code in ['incoming']:
                    self.update({'move_line_ids': [
                                (1, similar_lines[-1].id, {'quantity': quantity})]})
                if self.picking_code in ['outgoing', 'internal']:
                    self.update(
                        {'move_line_ids': [(1, similar_lines[-1].id, {'quantity': quantity})]})

                message = _('Product: %s<br /> Qty: %s') % (self.product_id.name, similar_lines[-1].quantity)
                self.sh_send_bus(company_sudo, "Succeed", message, 'success')

                if self.quantity == self.product_uom_qty + 1:
                    message = _(
                        'Be careful! Quantity exceed than initial demand!')
                    self.sh_send_bus(company_sudo, "Alert", message, 'warning')

    @api.onchange('sh_stock_move_barcode_mobile')
    def _onchange_sh_stock_move_barcode_mobile(self):
        if not self.sh_stock_move_barcode_mobile:
            return

        company_sudo = (self.company_id or self.env.company).sudo()

        if self.picking_id.state not in ['confirmed', 'assigned']:
            selections = self.picking_id.fields_get()['state']['selection']
            value = next((v[1] for v in selections if v[0] ==
                         self.picking_id.state), self.picking_id.state)

            message = _('You can not scan item in %s state.') % (value)
            self.sh_send_bus(company_sudo, "Failed", message, 'danger')
            return

        if self.sh_stock_move_barcode_mobile:
            if self.has_tracking != 'none':
                self.sh_stock_move_barcode_mobile_has_tracking(
                    company_sudo, self.sh_stock_move_barcode_mobile)

            else:
                self.sh_stock_move_barcode_mobile_no_tracking(
                    company_sudo, self.sh_stock_move_barcode_mobile)

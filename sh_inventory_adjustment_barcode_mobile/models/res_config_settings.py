# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sh_inventory_adjt_barcode_mobile_type = fields.Selection(
        related='company_id.sh_inventory_adjt_barcode_mobile_type', readonly=False)
    sh_inventory_adjt_bm_is_cont_scan = fields.Boolean(
        related='company_id.sh_inventory_adjt_bm_is_cont_scan', readonly=False)
    sh_inventory_adjt_bm_is_notify_on_success = fields.Boolean(
        related='company_id.sh_inventory_adjt_bm_is_notify_on_success', readonly=False)
    sh_inventory_adjt_bm_is_notify_on_fail = fields.Boolean(
        related='company_id.sh_inventory_adjt_bm_is_notify_on_fail', readonly=False)
    sh_inventory_adjt_bm_is_sound_on_success = fields.Boolean(
        related='company_id.sh_inventory_adjt_bm_is_sound_on_success', readonly=False)
    sh_inventory_adjt_bm_is_sound_on_fail = fields.Boolean(
        related='company_id.sh_inventory_adjt_bm_is_sound_on_fail', readonly=False)

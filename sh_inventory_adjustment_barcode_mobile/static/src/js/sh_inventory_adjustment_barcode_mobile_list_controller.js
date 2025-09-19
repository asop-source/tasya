/** @odoo-module **/

import { InventoryReportListView } from "@stock/views/list/inventory_report_list_view"
import { InventoryReportListController } from "@stock/views/list/inventory_report_list_controller";
import { browser } from "@web/core/browser/browser";
import { onWillStart, useRef, markup, useState } from "@odoo/owl";
import { escape } from "@web/core/utils/strings";
import { url } from "@web/core/utils/urls";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useDebounced } from "@web/core/utils/timing";
import { loadJS } from "@web/core/assets";
import { ShBarcodeMobile } from "../barcode_mobile/barcode_mobile";

export class InventoryAdjustmentBarcodeMobileListController extends InventoryReportListController {
    setup() {
        super.setup();
        this.alertMsgRef = useRef("alertMsg");
        this.inputBarcodeRef = useRef("inputBarcode");

        this.onChangeBarcodeMobileStockQuantInputDebounced = useDebounced(this.onChangeBarcodeMobileStockQuantInput, 500);
        onWillStart(this.willStart);
    }
    /** Lifecycle
     * Get Inventory Barcode Scanner configuration settings.
     */
    async willStart() {
        this.loadAudio();
        const result = await this.rpc('/sh_inventory_adjustment_barcode_mobile/get_widget_data');
        this.isStockManager = result.user_is_stock_manager || false;
        this.isContinuouslyScan = result.sh_inventory_adjt_bm_is_cont_scan || false
        this.hasStockMultiLocations = result.user_has_stock_multi_locations || false;
        this.stockLocations = result.locations || [];
        this.selectedStockLocationId = browser.localStorage.getItem('sh_inventory_adjustment_barcode_mobile_location_selected') !== undefined && !isNaN(browser.localStorage.getItem('sh_inventory_adjustment_barcode_mobile_location_selected')) ? parseInt(browser.localStorage.getItem("sh_inventory_adjustment_barcode_mobile_location_selected")) : 0;
        this.scanNegativeStock = browser.localStorage.getItem('sh_inventory_adjustment_barcode_mobile_is_scan_negative_stock') === "true" ? true : false;

    }

    loadAudio() {
        this.successAudio = new Audio();
        this.successAudio.src = url("/sh_inventory_adjustment_barcode_mobile/static/src/sounds/picked.wav");

        this.failAudio = new Audio();
        this.failAudio.src = url("/sh_inventory_adjustment_barcode_mobile/static/src/sounds/error.wav");
    }


    async onChangeLocationSelection(ev) {
        this.selectedStockLocationId = ev.target.value !== undefined && !isNaN(ev.target.value) ? parseInt(ev.target.value) : 0;
        browser.localStorage.setItem('sh_inventory_adjustment_barcode_mobile_location_selected', this.selectedStockLocationId);
    }

    async onChangeScanNegativeStockCheckBox(ev) {
        this.scanNegativeStock = ev.target.checked;
        browser.localStorage.setItem('sh_inventory_adjustment_barcode_mobile_is_scan_negative_stock', this.scanNegativeStock);
    }

    async onChangeBarcodeMobileStockQuantInput(ev) {
        let location = (this.stockLocations || []).filter(location => location?.id === this.selectedStockLocationId)
        if (this.stockLocations?.length && !location.length) {
            location = this.stockLocations[0];
            this.selectedStockLocationId = location.id !== undefined && !isNaN(location.id) ? parseInt(location.id) : 0;
            browser.localStorage.setItem('sh_inventory_adjustment_barcode_mobile_location_selected', this.selectedStockLocationId);
        }
        if (location && location.length) { this.location_name = location[0].display_name }

        const result = await this.rpc("/sh_all_in_one_mbs/sh_barcode_scanner_search_stock_quant_by_barcode", {
            domain: this.props.domain,
            barcode: ev.target.value,
            location_id: this.hasStockMultiLocations ? this.selectedStockLocationId : false,
            location_name: this.hasStockMultiLocations && this.location_name !== undefined ? this.location_name : "",
            scan_negative_stock: this.scanNegativeStock
        });
        if (result && result.is_qty_updated) {
            await this.model.root.load();
            this.render(true);
            if (this.alertMsgRef?.el) { $(this.alertMsgRef.el).html($('<div class="alert alert-info mt-3" role="alert">' + result.message + ' </div>')); }
        }
        else {
            if (this.alertMsgRef?.el) { $(this.alertMsgRef.el).html($('<div class="alert alert-danger mt-3" role="alert">' + result.message + ' </div>')); }
        }
    }

    async onClickStockQuantApply() {
        const result = await this.rpc('/sh_all_in_one_mbs/sh_barcode_scanner_stock_quant_tree_btn_apply', { domain: this.props.domain });

        let title = _t("Something went wrong");
        if (result && result.is_qty_applied) {
            title = _t("Inventory Succeed");
            await this.model.root.load();
            this.render(true);
        } else {
            title = _t("Something went wrong");
        }
        this.dialogService.add(ConfirmationDialog, {
            title: title,
            body: markup(`<p>${escape(result.message)}</p>`),
        });
    }

    handelMobileBarcode(barcode) {
        if(this.inputBarcodeRef){
            this.inputBarcodeRef.el.value=barcode
            this.inputBarcodeRef.el.dispatchEvent(new Event("change"));
            this.inputBarcodeRef.el.value=""
        }
    }

}
InventoryAdjustmentBarcodeMobileListController.components = {
    ...InventoryReportListController.components,
    ShBarcodeMobile:ShBarcodeMobile,
};
InventoryAdjustmentBarcodeMobileListController.template = "sh_inventory_adjustment_barcode_mobile.ListView";
InventoryReportListView.Controller = InventoryAdjustmentBarcodeMobileListController
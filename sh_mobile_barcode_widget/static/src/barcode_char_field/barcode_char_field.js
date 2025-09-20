/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadJS } from "@web/core/assets";
import { isBarcodeScannerSupported } from "@web/webclient/barcode/barcode_scanner";
import { isVideoElementReady } from "@web/webclient/barcode/ZXingBarcodeDetector";

import { delay } from "@web/core/utils/concurrency";
import { browser } from "@web/core/browser/browser";
import { onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { CharField, charField } from "@web/views/fields/char/char_field";

export class ShCharBarcode extends CharField {
    static template = "sh_mobile_barcode_widget.BarcodeCharField";

    static props = {
        ...CharField.props,
        continuouslyScanField: { type: String, optional: true },
    };
    /**
     * @override
     */
    setup() {
        super.setup();
        this.videoPreviewRef = useRef("videoPreview");
        this.selectCameraRef = useRef("selectCamera");

        this.notification = useService("notification");

        this.detector = null;
        this.stream = null;
        this.deviceId = browser.localStorage.getItem("sh_mobile_barcode_widget_selected_device_id") || null;
        this.formatReader = null;

        this.state = useState({
            isReady: false,
            isScanning: false,
            scannedBarcode: null
        });

        onWillStart(async () => {
            try {
                // Load Zxing Library
                await loadJS("/web/static/lib/zxing-library/zxing-library.js");
                // Set the format Reader = Zxings Browser Multi Format Reader
                this.formatReader = new window.ZXing.BrowserMultiFormatReader();
            } catch (err) {
                this.onError(err);
            }
        });

        onWillUnmount(() => {
            this.state.isScanning = false;
            if (this.stream) {
                this.stopStreams(this.stream)
            }
        });
    }

    get hasBarcodeButtons() {
        return isBarcodeScannerSupported();
    }
    get hasStopScanningBtn() {
        return this.state.isScanning;
    }
    get hasVideoPreview() {
        return this.state.isScanning;
    }

    get scannedBarcodeResult() {
        return this.state.scannedBarcode;
    }
    /**
     * The function checks if a video element is ready and sets a state variable accordingly.
     */
    async isVideoReady() {
        while (this.videoPreviewRef.el && !isVideoElementReady(this.videoPreviewRef.el)) {
            await delay(10);
        }
        this.state.isReady = true;
    }

    /**
     * Displays the Error message
     * @param {Object} err 
     * @returns notifier
     */
    onError(err) {
        const errors = {
            NotFoundError: _t("No device can be found."),
            NotAllowedError: _t("Odoo needs your authorization first."),
        };
        const errorMessage = _t("Could not start scanning. ") + (errors[err.name] || err.message);

        return this.notification.add(errorMessage, {
            title: _t("Warning"),
            type: "warning",
        });
    }

    /**
     * Stops the scan stream.
     */
    stopStreams(stream) {
        if (this.formatReader) {
            this.formatReader.reset();
        }
        if (stream) {
            stream.getVideoTracks().forEach(t => t.stop());
        }
        return null
    }

    /**
     * Render camera devices selection elements
     */
    async _renderCameraDevicesSelection() {
        // Get all supported camera devices
        const cameraDevices = await this.formatReader.listVideoInputDevices();
        if (cameraDevices && this.selectCameraRef.el) {
            cameraDevices.forEach(async (camera) => {
                const optionElement = document.createElement("option");
                optionElement.textContent = camera.label;
                optionElement.value = camera.deviceId;
                if (!this.deviceId) {
                    // select the first device option
                    await this.onChangeCameraSelection(camera.deviceId);
                    optionElement.setAttribute("selected", true);
                } else if (this.deviceId === camera.deviceId) {
                    // select option by device id
                    optionElement.setAttribute("selected", true);
                }
                this.selectCameraRef.el.append(optionElement);
            })
        }
    }

    /**
     * Render the video preview element
     */
    async _renderVideoPreview() {
        let videoConstraints;
        if (!this.deviceId) {
            videoConstraints = { facingMode: 'environment' };
        }
        else {
            videoConstraints = { deviceId: { exact: this.deviceId } };
        }

        const constraints = {
            video: videoConstraints,
            audio: false,
        };

        try {
            if (this.stream) {
                await this.stopStreams(this.stream)
            }
            this.state.isScanning = true;
            this.stream = await browser.navigator.mediaDevices.getUserMedia(constraints);
        } catch (err) {
            this.state.isScanning = false;
            return this.onError(err);
        }
        if (this.videoPreviewRef && this.videoPreviewRef.el) {
            this.videoPreviewRef.el.srcObject = this.stream;
        }
    }

    /**
     * Handel video preview by camera device
     * @param {string} deviceId the video input device id
     */
    async onChangeCameraSelection(deviceId) {
        if (deviceId) {
            browser.localStorage.setItem("sh_mobile_barcode_widget_selected_device_id", deviceId);
            this.deviceId = deviceId;
        }
        await this._renderVideoPreview();
        await this.detectCode();
    }

    /**
    * Attempt to detect codes in the current camera preview's frame
    */
    async detectCode() {
        var self = this;
        if (this.deviceId && this.videoPreviewRef.el) {
            try {
                if (this.props.continuouslyScanField && this.props.record.data[this.props.continuouslyScanField]) {
                    await this.formatReader.decodeFromVideoDevice(this.deviceId, this.videoPreviewRef.el, async (result, error) => {
                        if (result && result.text && !error) {
                            this.state.scannedBarcode = result.text;
                            await this.props.record.update({ [this.props.name]: result.text });
                            // await this.props.record.update({ [this.props.name]: false });
                        }
                    });
                } else {
                    const result = await this.formatReader.decodeOnceFromVideoDevice(this.deviceId, this.videoPreviewRef.el);
                    if (result.text) {
                        this.state.scannedBarcode = result.text;
                        await this.props.record.update({ [this.props.name]: result.text });
                        await this.onStopBarcodeScanning();
                        // await this.props.record.update({ [this.props.name]: false });
                        return
                    }
                }
            } catch (err) {
                // this.onError(err);
                if (err.name === "NotFoundException") {
                    return;
                }
                return

            }
        }
    }

    /**
     * Start scanning
     */
    async onStartBarcodeScanning() {
        this.state.isScanning = true;
        if (!this.formatReader) {
            this.state.isScanning = false;
            return
        }
        await this._renderCameraDevicesSelection();
        await this._renderVideoPreview();
        await this.isVideoReady();
        await this.detectCode();
    }
    /**
     * Stop scanning
     */
    async onStopBarcodeScanning() {
        if (this.stream) {
            await this.stopStreams(this.stream);
        }
        this.state.isScanning = false;
    }

}

export const shCharBarcode = {
    ...charField,
    component: ShCharBarcode,
    displayName: _t("CharBarcode"),
    supportedOptions: [
        ...(charField.supportedOptions || []),
        {
            label: _t("Continuously scan field"),
            name: "continuously_scan_field",
            type: "string",
        }
    ],
    extractProps({ options }) {
        const props = charField.extractProps(...arguments);
        props.continuouslyScanField = options.continuously_scan_field;
        return props

    }
};

registry.category("fields").add("sh_char_barcode", shCharBarcode);
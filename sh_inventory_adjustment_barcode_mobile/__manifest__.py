# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "Stock Adjustment Mobile Barcode/QRCode Scanner",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "version": "17.0.1.0.0",
    "category": "Inventory",
    "summary": "Scan Mobile Barcode Scan Tablet Barcode Scan Mobile Barcode Product Scan Product Internal Reference No Stock Barcode Scanner Inventory Barcode Scan Inventory Mobile Barcode Stock Mobile Barcode Scan Warehouse Adjustment Odoo Stock Adjustment Mobile QRCode Scanner Stock Adjustment Mobile Barcode Scanner Mobile QR code Scanner scan QR code Inventory Mobile Barcode Scanner Inventory Barcode Scanner Inventory QR code scanner app Stock Adjustment QR Scanner scan QRcode QR Scan Barcode scanning app Mobile QR code reader",
    "description": """Do you want to scan Barcode or QRCode in your mobile? Do your time wasting in Stock Adjustment operations by manual product selection ? So here is the solutions this modules useful do quick operations of Stock Adjustment mobile Barcode or QRCode scanner. You no need to select product and do one by one. scan it and you done! So be very quick in all operations of odoo in mobile and cheers!""",
    "depends": ["stock", "sh_product_qrcode_generator"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/stock_quant_views.xml",
    ],

    "assets": {
        "web.assets_backend": [
            "sh_inventory_adjustment_barcode_mobile/static/src/**/*"
        ],

    },


    "images": ["static/description/background.png", ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "price": 60,
    "currency": "EUR",
    "license": "OPL-1"
}

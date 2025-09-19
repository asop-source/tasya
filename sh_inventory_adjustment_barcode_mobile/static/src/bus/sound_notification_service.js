/* @odoo-module */

import { registry } from "@web/core/registry";
import { url } from "@web/core/utils/urls";
import { markup } from "@odoo/owl";

export const soundNotificationService = {
    dependencies: ["bus_service", "notification"],
    start(env, { bus_service, notification: notificationService }) {
        bus_service.subscribe("sound_notification", ({ message, sticky, title, type ,play_sound}) => {
            notificationService.add(markup(message), { sticky, title, type });
            if(play_sound){
                const audio = new Audio();
                audio.src = type === "success" ? url("/sh_inventory_adjustment_barcode_mobile/static/src/sounds/picked.wav") : url("/sh_inventory_adjustment_barcode_mobile/static/src/sounds/error.wav");
                audio.play();
            }
        });
        bus_service.start();
    },
};

registry.category("services").add("sound_notification", soundNotificationService);

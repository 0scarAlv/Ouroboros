/*
 * Light / dark theme.
 *
 * Loaded synchronously in <head> (no defer) so data-bs-theme is on <html>
 * before the first paint: no flash of the wrong theme. The choice is
 * "auto" (follow the OS, live), "light" or "dark", stored in localStorage;
 * the sidebar button [data-theme-switch] cycles through them.
 */
(function () {
    "use strict";

    var KEY = "ouroboros-theme";
    var ORDER = ["auto", "light", "dark"];
    var LABELS = { auto: "Automático", light: "Claro", dark: "Oscuro" };
    // Icons and a fallback from the current vendored subset, used until
    // scripts/update_vendor.py has added the new names to the font.
    var ICONS = { auto: "contrast", light: "light_mode", dark: "dark_mode" };
    var FALLBACK_ICONS = { auto: "sync", light: "visibility", dark: "visibility_off" };

    var media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

    function stored() {
        try {
            var value = window.localStorage.getItem(KEY);
            return ORDER.indexOf(value) >= 0 ? value : "auto";
        } catch (error) {
            return "auto"; // storage blocked (private mode, policy)
        }
    }

    function store(value) {
        try {
            window.localStorage.setItem(KEY, value);
        } catch (error) {
            // The choice then lasts only for this page.
        }
    }

    var choice = stored();

    function resolved() {
        if (choice !== "auto") return choice;
        return media && media.matches ? "dark" : "light";
    }

    function apply() {
        document.documentElement.setAttribute("data-bs-theme", resolved());
        document.documentElement.setAttribute("data-theme-choice", choice);
    }

    // An icon name missing from the font renders as its plain text, wider
    // than the 1em glyph box: swap in the fallback.
    function checkIcon(icon, fallback) {
        if (icon.scrollWidth > icon.offsetHeight * 1.5) icon.textContent = fallback;
    }

    function renderSwitches() {
        var next = ORDER[(ORDER.indexOf(choice) + 1) % ORDER.length];
        document.querySelectorAll("[data-theme-switch]").forEach(function (button) {
            var label = button.querySelector("[data-theme-label]");
            var icon = button.querySelector("[data-theme-icon]");
            if (label) label.textContent = "Tema: " + LABELS[choice];
            button.setAttribute("aria-label", "Tema: " + LABELS[choice] + ". Cambiar a " + LABELS[next]);
            button.title = "Cambiar a " + LABELS[next];
            if (icon) {
                icon.textContent = ICONS[choice];
                var fallback = FALLBACK_ICONS[choice];
                if (document.fonts && document.fonts.ready) {
                    document.fonts.ready.then(function () { checkIcon(icon, fallback); });
                } else {
                    checkIcon(icon, fallback);
                }
            }
        });
    }

    apply();

    if (media) {
        var onChange = function () { if (choice === "auto") apply(); };
        if (media.addEventListener) media.addEventListener("change", onChange);
        else if (media.addListener) media.addListener(onChange);
    }

    // Another tab changed the theme.
    window.addEventListener("storage", function (event) {
        if (event.key !== KEY) return;
        choice = stored();
        apply();
        renderSwitches();
    });

    document.addEventListener("click", function (event) {
        var button = event.target.closest && event.target.closest("[data-theme-switch]");
        if (!button) return;
        choice = ORDER[(ORDER.indexOf(choice) + 1) % ORDER.length];
        store(choice);
        apply();
        renderSwitches();
    });

    document.addEventListener("DOMContentLoaded", renderSwitches);
})();

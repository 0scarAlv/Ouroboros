/*
 * CRUD list page: row selection, the action toolbar and the panel above the
 * table (templates/crud/list.html).
 *
 * - Click a row (or move with the arrow keys) to select it; toolbar buttons
 *   that need a record are enabled when the selected row carries their URL
 *   (data-update-url, data-delete-url, data-history-url, data-detail-url).
 * - A toolbar action loads its view into #crud-panel-body through htmx; the
 *   panel slides open and the table stays below it.
 * - The toolbar button that opened the panel turns into "Cancelar"
 *   (aria-expanded="true") and closes it; another button moves that state
 *   to itself. Closing the panel by any route restores every label.
 * - Double-click, or Enter on the selected row, opens the default action
 *   (Modificar, or Ver without change permission). Esc closes the panel.
 * - After a successful change the server answers 204 with HX-Trigger
 *   `crudChanged`: the panel closes and the table reloads with the current
 *   URL (search and page are kept there by hx-push-url).
 *
 * Everything uses event delegation on document, so it survives table swaps,
 * and it does nothing on pages without [data-crud-list].
 */
(function () {
    "use strict";

    var CLOSE_DELAY = 260; // a bit longer than the CSS --motion

    var CANCEL_LABEL = "Cancelar";
    var CANCEL_ICON = "close";

    var pendingSelect = null; // pk to select after the table reloads
    var pendingAction = null; // toolbar action whose panel is loading

    function list() { return document.querySelector("[data-crud-list]"); }
    function panel() { return document.getElementById("crud-panel"); }
    function panelBody() { return document.getElementById("crud-panel-body"); }
    function table() { return document.getElementById("crud-table"); }

    function rows() {
        var t = table();
        return t ? Array.prototype.slice.call(t.querySelectorAll("tr[data-pk]")) : [];
    }

    function selectedRow() {
        var t = table();
        return t ? t.querySelector('tr[data-pk][aria-selected="true"]') : null;
    }

    function rowUrl(row, action) {
        return row ? row.getAttribute("data-" + action + "-url") : null;
    }

    function isPanelOpen() {
        var p = panel();
        return !!p && p.classList.contains("is-open");
    }

    // ---- Selection ---------------------------------------------------------

    function toolbarButtons() {
        var root = list();
        return root ? Array.prototype.slice.call(root.querySelectorAll("[data-crud-action]")) : [];
    }

    function updateToolbar() {
        var row = selectedRow();
        toolbarButtons().forEach(function (button) {
            if (button.tagName !== "BUTTON") return;
            // The active (Cancelar) button must stay usable to close the panel.
            var active = button.getAttribute("aria-expanded") === "true";
            button.disabled = !active && !rowUrl(row, button.getAttribute("data-crud-action"));
        });
    }

    // Mark the button of `action` as the one that opened the panel (it reads
    // "Cancelar"); null restores every button.
    function setActiveAction(action) {
        toolbarButtons().forEach(function (button) {
            var active = button.getAttribute("data-crud-action") === action;
            button.setAttribute("aria-expanded", active ? "true" : "false");
            var label = button.querySelector("[data-crud-label]");
            var icon = button.querySelector("[data-crud-icon]");
            if (label) label.textContent = active ? CANCEL_LABEL : button.getAttribute("data-label");
            if (icon) icon.textContent = active ? CANCEL_ICON : button.getAttribute("data-icon");
        });
        updateToolbar();
    }

    function selectRow(row, focus) {
        rows().forEach(function (other) {
            if (other !== row) {
                other.setAttribute("aria-selected", "false");
                other.tabIndex = -1;
            }
        });
        row.setAttribute("aria-selected", "true");
        row.tabIndex = 0;
        if (focus) row.focus();
        updateToolbar();
    }

    function focusTable() {
        var row = selectedRow() || rows()[0];
        if (row) row.focus();
    }

    // ---- Panel -------------------------------------------------------------

    function openUrl(url) {
        if (!url || !panelBody()) return;
        htmx.ajax("GET", url, { target: "#crud-panel-body", swap: "innerHTML" });
    }

    function runAction(action) {
        pendingAction = action;
        if (action === "create") {
            var link = list() && list().querySelector('[data-crud-action="create"]');
            openUrl(link && link.getAttribute("href"));
        } else {
            openUrl(rowUrl(selectedRow(), action));
        }
    }

    function runDefaultAction() {
        var root = list();
        var action = root && root.getAttribute("data-crud-default");
        if (action) runAction(action);
    }

    function showPanel() {
        var p = panel();
        var body = panelBody();
        body.removeAttribute("inert");
        p.classList.add("is-open");
        var target =
            body.querySelector("[autofocus]") ||
            body.querySelector(".is-invalid") ||
            body.querySelector("input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])") ||
            body.querySelector("button, a[href]");
        if (target) target.focus({ preventScroll: true });
        p.scrollIntoView({ block: "nearest", behavior: "auto" });
    }

    function closePanel(restoreFocus) {
        var p = panel();
        var body = panelBody();
        if (!p || !isPanelOpen()) return;
        p.classList.remove("is-open");
        body.setAttribute("inert", "");
        pendingAction = null;
        setActiveAction(null);
        // Empty it once the slide is over, unless it was reopened meanwhile.
        window.setTimeout(function () {
            if (!isPanelOpen()) body.innerHTML = "";
        }, CLOSE_DELAY);
        if (restoreFocus) focusTable();
    }

    function resetRestoredPage() {
        // Back/forward restores the page from htmx's history cache, which may
        // hold an open panel and a selected row: start clean instead.
        var p = panel();
        if (p) {
            p.classList.remove("is-open");
            panelBody().setAttribute("inert", "");
            panelBody().innerHTML = "";
        }
        pendingAction = null;
        setActiveAction(null);
        rows().forEach(function (row, index) {
            row.setAttribute("aria-selected", "false");
            row.tabIndex = index === 0 ? 0 : -1;
        });
        updateToolbar();
    }

    function reloadTable() {
        htmx.ajax("GET", window.location.pathname + window.location.search, {
            target: "#crud-table",
            swap: "innerHTML",
        });
    }

    // ---- Events ------------------------------------------------------------

    document.addEventListener("click", function (event) {
        if (!list()) return;

        var actionEl = event.target.closest("[data-crud-action]");
        if (actionEl) {
            // Nuevo is a link so it also works without JS; let Ctrl/middle-click open a tab.
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) return;
            event.preventDefault();
            if (actionEl.disabled) return;
            if (actionEl.getAttribute("aria-expanded") === "true") {
                closePanel(true); // the button reads "Cancelar"
            } else {
                runAction(actionEl.getAttribute("data-crud-action"));
            }
            return;
        }

        if (event.target.closest("[data-crud-close]")) {
            event.preventDefault();
            closePanel(true);
            return;
        }

        var row = event.target.closest("#crud-table tr[data-pk]");
        if (row) selectRow(row, true);
    });

    document.addEventListener("dblclick", function (event) {
        var row = list() && event.target.closest("#crud-table tr[data-pk]");
        if (!row) return;
        selectRow(row, true);
        runDefaultAction();
    });

    document.addEventListener("keydown", function (event) {
        if (!list()) return;

        if (event.key === "Escape" && isPanelOpen()) {
            // Leave Esc to an open Bootstrap dropdown or modal.
            if (document.querySelector(".modal.show, .dropdown-menu.show")) return;
            event.preventDefault();
            closePanel(true);
            return;
        }

        var row = event.target.closest && event.target.closest("#crud-table tr[data-pk]");
        if (!row || event.altKey || event.ctrlKey || event.metaKey) return;

        var all = rows();
        var index = all.indexOf(row);
        var next = null;

        switch (event.key) {
            case "ArrowDown": next = all[index + 1]; break;
            case "ArrowUp": next = all[index - 1]; break;
            case "Home": next = all[0]; break;
            case "End": next = all[all.length - 1]; break;
            case " ":
                event.preventDefault();
                selectRow(row, true);
                return;
            case "Enter":
                event.preventDefault();
                if (row.getAttribute("aria-selected") === "true") {
                    runDefaultAction();
                } else {
                    selectRow(row, true);
                }
                return;
            default:
                return;
        }
        event.preventDefault();
        if (next) selectRow(next, true);
    });

    document.addEventListener("htmx:afterSwap", function (event) {
        var target = event.detail.target;
        if (!target) return;

        if (target.id === "crud-panel-body") {
            // A form re-rendered with errors keeps the current active button.
            if (pendingAction) setActiveAction(pendingAction);
            pendingAction = null;
            showPanel();
        } else if (target.id === "crud-table") {
            // New rows: nothing is selected unless a change asked for it.
            var row = pendingSelect && table().querySelector('tr[data-pk="' + CSS.escape(pendingSelect) + '"]');
            pendingSelect = null;
            if (row) {
                selectRow(row, true);
            } else {
                updateToolbar();
                if (!document.activeElement || document.activeElement === document.body) focusTable();
            }
        }
    });

    // 204 + HX-Trigger from a successful create, update or delete.
    document.addEventListener("crudChanged", function (event) {
        if (!list()) return;
        var detail = event.detail || {};
        pendingSelect = detail.action === "delete" ? null : detail.pk || null;
        closePanel(false);
        reloadTable();
    });

    document.addEventListener("htmx:historyRestore", function () {
        if (list()) resetRestoredPage();
    });

    // A failed request (no permission, record already deleted, server error)
    // would otherwise do nothing visible.
    document.addEventListener("htmx:responseError", function (event) {
        if (!list()) return;
        pendingAction = null;
        var status = event.detail.xhr ? event.detail.xhr.status : 0;
        var message = {
            403: "No tiene permiso para esta acción.",
            404: "El registro ya no existe.",
        }[status] || "No se pudo completar la acción (error " + status + ").";
        showToast(message, "danger");
        if (status === 404) {
            closePanel(false);
            reloadTable();
        }
    });

    document.addEventListener("htmx:sendError", function () {
        if (list()) showToast("Sin conexión con el servidor.", "danger");
    });
})();

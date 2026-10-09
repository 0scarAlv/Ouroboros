function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");

    // Colours come from the --c-toast-* tokens (styles.css), so they follow
    // the theme; the icon tells success from info without relying on colour.
    const kind = ["success", "danger", "warning", "info"].includes(type) ? type : "info";
    const icon = { success: "check_circle", danger: "error", warning: "warning", info: "info" }[kind];

    const toastEl = document.createElement("div");
    toastEl.className = `toast toast--${kind} align-items-center`;
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");

    toastEl.innerHTML = `
        <div class="d-flex align-items-center">
            <span class="icon ms-3" aria-hidden="true"></span>
            <div class="toast-body fw-semibold"></div>
            <button
                type="button"
                class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast"
                aria-label="Cerrar">
            </button>
        </div>
    `;
    toastEl.querySelector(".icon").textContent = icon;
    // textContent, never innerHTML: messages may contain user-entered text.
    toastEl.querySelector(".toast-body").textContent = message;

    container.appendChild(toastEl);

    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();

    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}

// Listens for HTMX showToast event triggered via HX-Trigger response header
document.body.addEventListener("showToast", function (event) {
    const { message, type } = event.detail;
    showToast(message, type);
});

// Django messages rendered by base.html after a redirect
document.querySelectorAll("#flash-messages li").forEach(function (item) {
    showToast(item.textContent, item.dataset.type);
});

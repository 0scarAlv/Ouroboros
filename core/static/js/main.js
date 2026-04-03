function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");

    // Map type to Bootstrap bg utility class
    const bgClass = {
        success: "bg-success",
        danger:  "bg-danger",
        warning: "bg-warning",
        info:    "bg-info",
    }[type] || "bg-secondary";

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-white ${bgClass} border-0`;
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");

    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-semibold">${message}</div>
            <button
                type="button"
                class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast"
                aria-label="Close">
            </button>
        </div>
    `;

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
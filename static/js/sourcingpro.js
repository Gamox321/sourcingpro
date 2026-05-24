function actualizarNotificaciones() {
    var countEl = document.getElementById('notif-count');
    if (!countEl) return;
    fetch('/notificaciones/contar/')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            countEl.textContent = data.count;
            countEl.style.display = data.count > 0 ? 'inline' : 'none';
            countEl.className = 'badge badge-counter';
            if (data.count > 0) {
                countEl.classList.add(data.count >= 10 ? 'bg-danger' : data.count >= 5 ? 'bg-warning' : 'bg-primary');
            }
        });
    fetch('/notificaciones/dropdown/')
        .then(function (r) { return r.text(); })
        .then(function (html) {
            var el = document.getElementById('notif-dropdown');
            if (el) el.innerHTML = html;
        });
}

function iniciarSpinnerSubmit() {
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            var btn = this.querySelector('button[type="submit"]');
            if (btn && !btn.dataset.noSpinner) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> ' + btn.textContent.trim();
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
            var bsAlert = new bootstrap.Alert(alert);
            setTimeout(function () { bsAlert.close(); }, 5000);
        });
    }, 100);

    actualizarNotificaciones();
    setInterval(actualizarNotificaciones, 30000);
    var bell = document.getElementById('alertsDropdown');
    if (bell) {
        bell.addEventListener('shown.bs.dropdown', function () {
            actualizarNotificaciones();
        });
    }

    iniciarSpinnerSubmit();
});

function actualizarNotificaciones() {
    var countEl = document.getElementById('notif-count');
    if (!countEl) return;
    fetch('/notificaciones/contar/')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            countEl.textContent = data.count;
            countEl.style.display = data.count > 0 ? 'inline' : 'none';
        });
    fetch('/notificaciones/dropdown/')
        .then(function (r) { return r.text(); })
        .then(function (html) {
            var el = document.getElementById('notif-dropdown');
            if (el) el.innerHTML = html;
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
});

/* ------------------------------------------------------------------ */
/*  Notifications                                                      */
/* ------------------------------------------------------------------ */
function toast(message, type) {
    type = type || 'info';
    var icons = {
        'success': 'fa-check-circle text-success',
        'error': 'fa-exclamation-circle text-danger',
        'warning': 'fa-exclamation-triangle text-warning',
        'info': 'fa-info-circle text-primary'
    };
    var iconClass = icons[type] || icons['info'];
    var el = document.createElement('div');
    el.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;background:#fff;border-radius:8px;padding:12px 16px;box-shadow:0 4px 12px rgba(0,0,0,0.15);display:flex;align-items:center;gap:10px;min-width:200px;max-width:350px;animation:slideInToast 0.3s ease';
    el.innerHTML = '<i class="fas ' + iconClass + '"></i><span style="flex:1;font-size:14px">' + message + '</span>';
    document.body.appendChild(el);
    setTimeout(function () {
        el.style.animation = 'slideOutToast 0.3s ease';
        setTimeout(function () { el.remove(); }, 300);
    }, 3500);
}

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
        })
        .catch(function () {
            var offlineEl = document.getElementById('notif-offline');
            if (offlineEl) offlineEl.style.display = 'inline';
        });
    fetch('/notificaciones/dropdown/')
        .then(function (r) { return r.text(); })
        .then(function (html) {
            var el = document.getElementById('notif-dropdown');
            if (el) el.innerHTML = html;
        })
        .catch(function () {});
}

/* ------------------------------------------------------------------ */
/*  Form submit spinner                                                 */
/* ------------------------------------------------------------------ */
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

/* ------------------------------------------------------------------ */
/*  Confirmation modal (replaces confirm())                             */
/* ------------------------------------------------------------------ */
function iniciarConfirmModal() {
    var modalEl = document.getElementById('confirmModal');
    if (!modalEl) return;
    var modal = new bootstrap.Modal(modalEl);
    var bodyEl = document.getElementById('confirmModalBody');
    var btnEl = document.getElementById('confirmModalBtn');
    var pendingForm = null;
    var pendingCallback = null;

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-confirm]');
        if (!btn) return;
        e.preventDefault();
        bodyEl.textContent = btn.dataset.confirm;
        pendingForm = btn.closest('form');
        pendingCallback = null;
        modal.show();
    });

    document.addEventListener('submit', function (e) {
        var form = e.target;
        var btn = form.querySelector('[data-confirm]');
        var formConfirm = form.dataset.confirmForm;
        if (!btn && !formConfirm) return;
        e.preventDefault();
        bodyEl.textContent = formConfirm || btn.dataset.confirm;
        pendingForm = form;
        pendingCallback = null;
        modal.show();
    });

    btnEl.addEventListener('click', function () {
        modal.hide();
        if (pendingCallback) {
            pendingCallback();
            pendingCallback = null;
        } else if (pendingForm) {
            var submitBtn = pendingForm.querySelector('[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;
            pendingForm.submit();
            pendingForm = null;
        }
    });
}

/* ------------------------------------------------------------------ */
/*  Session countdown (moved from inline script)                        */
/* ------------------------------------------------------------------ */
function iniciarSesionCountdown() {
    if (window.__sessionRemaining === undefined) return;
    var remaining = window.__sessionRemaining;
    var warningShown = false;
    var countdownInterval = null;

    function actualizarCuentaAtras() {
        var minutes = Math.floor(remaining / 60);
        var seconds = remaining % 60;
        var el = document.getElementById('sessionCountdown');
        if (el) el.textContent = String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');

        if (remaining <= 600 && !warningShown) {
            warningShown = true;
            var toastEl = document.getElementById('sessionToast');
            if (toastEl) {
                var toast = new bootstrap.Toast(toastEl, { autohide: false });
                toast.show();
            }
        }

        if (remaining <= 0) {
            clearInterval(countdownInterval);
            if (window.__logoutUrl) window.location.href = window.__logoutUrl;
        }

        remaining--;
    }

    if (remaining > 0) {
        countdownInterval = setInterval(actualizarCuentaAtras, 1000);
        actualizarCuentaAtras();
    }
}

/* ------------------------------------------------------------------ */
/*  Live search with debounce                                           */
/* ------------------------------------------------------------------ */
function iniciarBusquedaViva() {
    document.querySelectorAll('[data-search]').forEach(function (input) {
        var timer = null;
        input.addEventListener('input', function () {
            clearTimeout(timer);
            timer = setTimeout(function () {
                var form = input.closest('form');
                if (form) form.submit();
            }, 400);
        });
    });
}

/* ------------------------------------------------------------------ */
/*  Keyboard shortcuts                                                  */
/* ------------------------------------------------------------------ */
function iniciarAtajosTeclado() {
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            var modals = document.querySelectorAll('.modal.show');
            for (var i = 0; i < modals.length; i++) {
                var instance = bootstrap.Modal.getInstance(modals[i]);
                if (instance) instance.hide();
            }
        }
    });
}

/* ------------------------------------------------------------------ */
/*  Form dirty-check (beforeunload)                                     */
/* ------------------------------------------------------------------ */
function iniciarDirtyCheck() {
    var dirty = false;
    document.addEventListener('change', function (e) {
        if (e.target.closest('form') && e.target.closest('[data-dirty]')) {
            dirty = true;
        }
    });
    document.addEventListener('input', function (e) {
        if (e.target.closest('form') && e.target.closest('[data-dirty]')) {
            dirty = true;
        }
    });
    document.querySelectorAll('form[data-dirty]').forEach(function (form) {
        form.addEventListener('submit', function () { dirty = false; });
    });
    window.addEventListener('beforeunload', function (e) {
        if (dirty) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}

/* ------------------------------------------------------------------ */
/*  Copy to clipboard                                                   */
/* ------------------------------------------------------------------ */
function iniciarClipboard() {
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-copy]');
        if (!btn) return;
        var text = btn.dataset.copy;
        if (!text) text = btn.textContent.trim();
        navigator.clipboard.writeText(text).then(function () {
            var original = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(function () { btn.innerHTML = original; }, 1500);
        });
    });
}

/* ------------------------------------------------------------------ */
/*  Bootstrap initialisation                                            */
/* ------------------------------------------------------------------ */
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
    iniciarConfirmModal();
    iniciarSesionCountdown();
    iniciarBusquedaViva();
    iniciarAtajosTeclado();
    iniciarClipboard();
});

/* Toast animations */
var styleEl = document.createElement('style');
styleEl.textContent = ''
    + '@keyframes slideInToast { from { transform: translateX(120%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }'
    + '@keyframes slideOutToast { from { transform: translateX(0); opacity: 1; } to { transform: translateX(120%); opacity: 0; } }';
document.head.appendChild(styleEl);

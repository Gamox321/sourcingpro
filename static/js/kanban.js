/* ------------------------------------------------------------------ */
/*  Kanban — SortableJS + event delegation                              */
/* ------------------------------------------------------------------ */

/* Initialise Sortable on each column */
function iniciarSortable() {
    document.querySelectorAll('.kanban-column').forEach(function (col) {
        new Sortable(col, {
            group: 'kanban',
            animation: 150,
            ghostClass: 'bg-light',
            onEnd: function (evt) {
                var card = evt.item;
                if (!card || !card.dataset.taskId) return;
                var taskId = card.dataset.taskId;
                var columnName = evt.to.dataset.column || 'pendientes';

                var estadoMap = {
                    'pendientes': 'pendiente',
                    'en-proceso': 'en_proceso',
                    'completadas': 'completada'
                };
                var nuevoEstado = estadoMap[columnName] || 'pendiente';

                actualizarTarea(taskId, nuevoEstado);
            }
        });
    });
}

/* API call to update task state */
function actualizarTarea(taskId, estado) {
    var card = document.querySelector('[data-task-id="' + taskId + '"]');
    fetch('/kanban/tarea/' + taskId + '/actualizar/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'estado=' + encodeURIComponent(estado),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        /* Success feedback */
        if (card) {
            card.style.transition = 'background-color 0.3s';
            card.style.backgroundColor = '#d4edda';
            setTimeout(function () {
                card.style.backgroundColor = '';
            }, 800);
        }
        toast('Tarea actualizada', 'success');
        actualizarIndicadorCarga();
    })
    .catch(function () {
        alert('Error al guardar. Intenta de nuevo.');
    });
}

/* Open card detail modal */
function abrirDetalle(taskId) {
    var modalEl = document.getElementById('cardDetailModal');
    if (!modalEl) return;
    var modal = new bootstrap.Modal(modalEl);
    var content = document.getElementById('cardDetailContent');
    content.innerHTML = '<div class="modal-body text-center py-5"><i class="fas fa-spinner fa-spin fa-2x"></i><p class="mt-2">Cargando...</p></div>';
    modal.show();

    var controller = new AbortController();
    var timeout = setTimeout(function () { controller.abort(); }, 10000);

    fetch('/kanban/tarea/' + taskId + '/', { headers: { 'HX-Request': 'true' }, signal: controller.signal })
        .then(function (r) { return r.text(); })
        .then(function (html) {
            clearTimeout(timeout);
            content.innerHTML = html;
        })
        .catch(function (err) {
            clearTimeout(timeout);
            if (err.name === 'AbortError') {
                content.innerHTML = '<div class="modal-body text-center py-5">' +
                    '<i class="fas fa-clock fa-2x text-muted mb-3 d-block"></i>' +
                    '<p class="text-muted">Tiempo de espera excedido.</p>' +
                    '<button class="btn btn-primary btn-sm" onclick="abrirDetalle(' + taskId + ')">' +
                    '<i class="fas fa-redo me-1"></i>Reintentar</button>' +
                    '</div>';
            } else {
                content.innerHTML = '<div class="modal-body text-center py-5">' +
                    '<i class="fas fa-exclamation-triangle fa-2x text-danger mb-3 d-block"></i>' +
                    '<p class="text-muted">Error al cargar los detalles.</p>' +
                    '<button class="btn btn-primary btn-sm" onclick="abrirDetalle(' + taskId + ')">' +
                    '<i class="fas fa-redo me-1"></i>Reintentar</button>' +
                    '</div>';
            }
        });
}

/* Reload load indicator */
function actualizarIndicadorCarga() {
    fetch('/kanban/carga/', { headers: { 'HX-Request': 'true' } })
        .then(function (r) { return r.text(); })
        .then(function (html) {
            var el = document.getElementById('load-indicator');
            if (el) el.innerHTML = html;
        });
}

/* CSRF helper */
function getCSRFToken() {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var c = cookies[i].trim();
        if (c.startsWith('csrftoken=')) {
            return c.substring('csrftoken='.length);
        }
    }
    return '';
}

/* ------------------------------------------------------------------ */
/*  Event delegation — replaces onclick in templates                    */
/* ------------------------------------------------------------------ */
document.addEventListener('DOMContentLoaded', function () {
    iniciarSortable();

    /* Click on a kanban card → open detail modal */
    document.addEventListener('click', function (e) {
        var card = e.target.closest('[data-task-id]');
        if (card && !e.target.closest('a, button, .dropdown-menu, .dropdown-toggle')) {
            abrirDetalle(card.dataset.taskId);
        }
    });

    /* Click on a state-change dropdown item → update task */
    document.addEventListener('click', function (e) {
        var item = e.target.closest('[data-cambiar-estado]');
        if (!item) return;
        e.preventDefault();
        actualizarTarea(item.dataset.taskId, item.dataset.cambiarEstado);
        var modal = bootstrap.Modal.getInstance(document.getElementById('cardDetailModal'));
        if (modal) modal.hide();
    });

    /* "Show archived" checkbox auto-submit */
    document.addEventListener('change', function (e) {
        if (e.target.matches('#archivadas')) {
            e.target.closest('form').submit();
        }
    });
});

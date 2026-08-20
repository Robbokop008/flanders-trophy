/**
 * static/js/admin_page_canvas.js
 * ---------------------------------
 * Bewerkscherm voor een contentpagina (templates/admin/page_canvas.html):
 * de blokken worden getoond zoals ze echt op de pagina staan, met sleep-
 * herordening. Verdere inline-bewerkfunctionaliteit wordt in latere fases
 * van de page-builder-uitbreiding toegevoegd.
 */
(function () {
    var list = document.getElementById('canvas-list');
    if (!list) return;

    var csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    var pageId = list.dataset.pageId;

    new Sortable(list, {
        handle: '.canvas-drag-handle',
        animation: 150,
        onEnd: function () {
            var items = Array.from(list.children).map(function (el, index) {
                return { id: parseInt(el.dataset.blockId, 10), position: index + 1 };
            });
            fetch('/admin/pages/' + pageId + '/blocks/reorder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ items: items }),
            });
        },
    });
})();

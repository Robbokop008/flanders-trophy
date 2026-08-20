/**
 * static/js/admin_rich_editor.js
 * ---------------------------------
 * Gedeelde Quill-initialisatie voor de admin rich-text editors (pagina's en
 * nieuwsberichten): afbeeldingen uploaden via de server, en tabellen
 * invoegen/bewerken via Quill's ingebouwde table-module.
 *
 * Verwacht een element met id "quill-editor" en de volgende data-attributen:
 *   data-textarea-id       id van de verborgen textarea die de HTML bij submit ontvangt
 *   data-image-upload-url  URL van het admin-upload-endpoint voor afbeeldingen
 */
(function () {
    var currentTableMenu = null;

    function closeTableMenu() {
        if (currentTableMenu) {
            currentTableMenu.remove();
            currentTableMenu = null;
            document.removeEventListener('mousedown', handleOutsideClick);
        }
    }

    function handleOutsideClick(evt) {
        if (currentTableMenu && !currentTableMenu.contains(evt.target)) {
            closeTableMenu();
        }
    }

    function openTableMenu(anchorEl, actions) {
        closeTableMenu();
        var menu = document.createElement('div');
        menu.className = 'ql-table-dropdown';
        actions.forEach(function (action) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.textContent = action.label;
            if (action.danger) btn.classList.add('ql-table-dropdown-danger');
            btn.addEventListener('click', function () {
                closeTableMenu();
                action.run();
            });
            menu.appendChild(btn);
        });
        document.body.appendChild(menu);
        var rect = anchorEl.getBoundingClientRect();
        menu.style.top = (window.scrollY + rect.bottom + 4) + 'px';
        menu.style.left = (window.scrollX + rect.left) + 'px';
        currentTableMenu = menu;
        setTimeout(function () { document.addEventListener('mousedown', handleOutsideClick); }, 0);
    }

    function askTableSize(callback) {
        var overlay = document.createElement('div');
        overlay.className = 'table-size-overlay';
        overlay.innerHTML =
            '<div class="table-size-dialog">' +
                '<h3>Tabel invoegen</h3>' +
                '<label>Rijen <input type="number" id="table-size-rows" value="3" min="1" max="20"></label>' +
                '<label>Kolommen <input type="number" id="table-size-cols" value="3" min="1" max="10"></label>' +
                '<div class="table-size-actions">' +
                    '<button type="button" class="btn btn-secondary btn-sm" data-action="cancel">Annuleren</button>' +
                    '<button type="button" class="admin-button btn-sm" data-action="ok">Invoegen</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(overlay);

        function close() { overlay.remove(); }
        overlay.querySelector('[data-action="cancel"]').addEventListener('click', close);
        overlay.addEventListener('click', function (evt) { if (evt.target === overlay) close(); });
        overlay.querySelector('[data-action="ok"]').addEventListener('click', function () {
            var rows = Math.min(20, Math.max(1, parseInt(overlay.querySelector('#table-size-rows').value, 10) || 1));
            var cols = Math.min(10, Math.max(1, parseInt(overlay.querySelector('#table-size-cols').value, 10) || 1));
            close();
            callback(rows, cols);
        });
    }

    function initAdminRichEditor(editorEl) {
        var textarea = document.getElementById(editorEl.dataset.textareaId);
        var uploadUrl = editorEl.dataset.imageUploadUrl;
        var csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        var quill;

        function imageHandler() {
            var input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.onchange = function () {
                var file = input.files[0];
                if (!file) return;
                var formData = new FormData();
                formData.append('image', file);
                fetch(uploadUrl, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: formData,
                })
                    .then(function (res) { return res.json(); })
                    .then(function (data) {
                        if (data.url) {
                            var range = quill.getSelection(true) || { index: quill.getLength() };
                            quill.insertEmbed(range.index, 'image', data.url, 'user');
                            quill.setSelection(range.index + 1);
                        } else {
                            alert(data.error || 'Uploaden van de afbeelding is mislukt.');
                        }
                    })
                    .catch(function () { alert('Uploaden van de afbeelding is mislukt.'); });
            };
            input.click();
        }

        function tableInsertHandler() {
            askTableSize(function (rows, cols) {
                quill.focus();
                quill.getModule('table').insertTable(rows, cols);
            });
        }

        function tableMenuHandler() {
            var range = quill.getSelection();
            var format = range ? quill.getFormat(range) : {};
            if (!format.table) {
                alert('Plaats de cursor eerst in een tabelcel om een rij of kolom toe te voegen of te verwijderen.');
                return;
            }
            var table = quill.getModule('table');
            var btn = quill.getModule('toolbar').container.querySelector('.ql-table-menu');
            openTableMenu(btn, [
                { label: 'Rij boven invoegen', run: function () { table.insertRowAbove(); } },
                { label: 'Rij onder invoegen', run: function () { table.insertRowBelow(); } },
                { label: 'Kolom links invoegen', run: function () { table.insertColumnLeft(); } },
                { label: 'Kolom rechts invoegen', run: function () { table.insertColumnRight(); } },
                { label: 'Rij verwijderen', run: function () { table.deleteRow(); }, danger: true },
                { label: 'Kolom verwijderen', run: function () { table.deleteColumn(); }, danger: true },
                {
                    label: 'Volledige tabel verwijderen',
                    danger: true,
                    run: function () {
                        if (confirm('Deze tabel volledig verwijderen?')) table.deleteTable();
                    },
                },
            ]);
        }

        quill = new Quill(editorEl, {
            theme: 'snow',
            modules: {
                table: true,
                toolbar: {
                    container: [
                        [{ header: [2, 3, 4, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ list: 'ordered' }, { list: 'bullet' }],
                        ['blockquote', 'link', 'image', 'video'],
                        ['table', 'table-menu'],
                        ['clean'],
                    ],
                    handlers: {
                        image: imageHandler,
                        table: tableInsertHandler,
                        'table-menu': tableMenuHandler,
                    },
                },
            },
        });

        var toolbarEl = quill.getModule('toolbar').container;
        var videoBtn = toolbarEl.querySelector('.ql-video');
        if (videoBtn) videoBtn.title = 'Video invoegen (YouTube/Vimeo-link)';
        var insertBtn = toolbarEl.querySelector('.ql-table');
        if (insertBtn) insertBtn.title = 'Tabel invoegen';
        var menuBtn = toolbarEl.querySelector('.ql-table-menu');
        if (menuBtn) {
            menuBtn.textContent = '⋮';
            menuBtn.title = 'Rij/kolom toevoegen of verwijderen (cursor moet in de tabel staan)';
            menuBtn.classList.add('ql-table-menu-btn');
        }

        quill.root.innerHTML = textarea.value;

        textarea.closest('form').addEventListener('submit', function () {
            textarea.value = quill.root.innerHTML;
        });

        return quill;
    }

    window.initAdminRichEditor = initAdminRichEditor;
})();

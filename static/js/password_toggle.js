/*
 * static/js/password_toggle.js
 * ------------------------------
 * Maakt elk "oogje"-knopje (.password-toggle) werkend: toont/verbergt de
 * ingevoerde tekens van het bijhorende wachtwoordveld. Het gekoppelde veld
 * wordt gevonden via data-toggle-for="<input id>". Geen effect als de
 * pagina geen .password-toggle-knoppen bevat.
 */
(function () {
    const EYE = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
    const EYE_OFF = '<path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a20.62 20.62 0 0 1 5.06-5.94M9.9 4.24A10.4 10.4 0 0 1 12 4c7 0 11 8 11 8a20.7 20.7 0 0 1-3.22 4.44M14.12 14.12a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';

    document.querySelectorAll('.password-toggle').forEach((button) => {
        const input = document.getElementById(button.dataset.toggleFor);
        const icon = button.querySelector('svg');
        if (!input || !icon) return;

        button.addEventListener('click', () => {
            const nowShowing = input.type === 'password';
            input.type = nowShowing ? 'text' : 'password';
            icon.innerHTML = nowShowing ? EYE_OFF : EYE;
            button.setAttribute('aria-label', nowShowing ? 'Wachtwoord verbergen' : 'Wachtwoord tonen');
            button.setAttribute('aria-pressed', String(nowShowing));
        });
    });
})();

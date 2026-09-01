/**
 * cookie_consent.js
 * ------------------
 * Toont de cookiebanner (zie #cookie-banner in templates/base.html) zolang
 * er geen bewaarde keuze is, en laadt Google Analytics pas nadat een
 * bezoeker expliciet op "Accepteren" klikt. Dit bestand wordt enkel geladen
 * als er een GA-meet-ID geconfigureerd is (zie app.py inject_analytics_config)
 * - window.GOOGLE_ANALYTICS_ID staat dan altijd klaar.
 */
(function () {
    "use strict";

    var STORAGE_KEY = "ft_cookie_consent";
    var banner = document.getElementById("cookie-banner");
    var acceptButton = document.getElementById("cookie-accept");
    var rejectButton = document.getElementById("cookie-reject");
    var settingsLink = document.getElementById("cookie-settings-link");

    function opgeslagenKeuze() {
        try {
            return window.localStorage.getItem(STORAGE_KEY);
        } catch (err) {
            // Privé-browsen/geblokkeerde opslag: gedraag je alsof er nog
            // geen keuze is, i.p.v. te crashen.
            return null;
        }
    }

    function bewaarKeuze(keuze) {
        try {
            window.localStorage.setItem(STORAGE_KEY, keuze);
        } catch (err) {
            // Kon niet bewaard worden - de banner verschijnt dan gewoon
            // opnieuw bij een volgend bezoek, geen harde fout nodig.
        }
    }

    function toonBanner() {
        if (banner) { banner.hidden = false; }
    }

    function verbergBanner() {
        if (banner) { banner.hidden = true; }
    }

    function laadGoogleAnalytics() {
        var gaId = window.GOOGLE_ANALYTICS_ID;
        if (!gaId || window.__gaGeladen) { return; }
        window.__gaGeladen = true;

        var script = document.createElement("script");
        script.async = true;
        script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(gaId);
        document.head.appendChild(script);

        window.dataLayer = window.dataLayer || [];
        function gtag() { window.dataLayer.push(arguments); }
        window.gtag = gtag;
        gtag("js", new Date());
        // anonymize_ip: extra voorzichtigheidsmaatregel bovenop wat GA4
        // standaard al doet - zie de privacybeleid-pagina (routes/pages.py
        // ensure_privacy_policy_page).
        gtag("config", gaId, { anonymize_ip: true });
    }

    if (acceptButton) {
        acceptButton.addEventListener("click", function () {
            bewaarKeuze("granted");
            verbergBanner();
            laadGoogleAnalytics();
        });
    }

    if (rejectButton) {
        rejectButton.addEventListener("click", function () {
            bewaarKeuze("denied");
            verbergBanner();
        });
    }

    if (settingsLink) {
        settingsLink.addEventListener("click", function (event) {
            event.preventDefault();
            toonBanner();
        });
    }

    var keuze = opgeslagenKeuze();
    if (keuze === "granted") {
        laadGoogleAnalytics();
    } else if (keuze !== "denied") {
        toonBanner();
    }
})();

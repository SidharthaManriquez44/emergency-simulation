(function () {
    "use strict";

    const KEY = "sidhartha-language";
    const buttons = Array.from(document.querySelectorAll("[data-site-lang]"));
    const banner = document.getElementById("project-banner");

    const content = {
        es: {
            project: "Simulación de Urgencias",
            nav: ["Investigación", "Modelo clínico", "Elemento de revisión", "Equipo de investigación"],
            login: "INICIAR SESIÓN",
            eyebrow: "SIMULACIÓN CLÍNICA",
            title: ["Optimización del", "proceso de atención", "en urgencias"],
            lead: "Reformulación · Modelado · Validación interdisciplinaria",
            explore: "EXPLORAR INVESTIGACIÓN →",
            review: "REVISIÓN DEL MODELO CLÍNICO →",
            quote: ["“Mejores decisiones", "para una atención", "oportuna y segura”"],
            banner: "assets/images/banner-es.png",
            bannerAlt: "Problema, sistema y modelo de simulación de urgencias"
        },
        en: {
            project: "Emergency Simulation",
            nav: ["Research", "Clinical Model", "Review Item", "Research Team"],
            login: "SIGN IN",
            eyebrow: "CLINICAL SIMULATION",
            title: ["Optimization of the", "Emergency Department", "Care Process"],
            lead: "Reformulation · Modeling · Interdisciplinary Validation",
            explore: "EXPLORE RESEARCH →",
            review: "CLINICAL MODEL REVIEW →",
            quote: ["“Better decisions", "for timely and", "safe care”"],
            banner: "assets/images/banner-en.png",
            bannerAlt: "Problem, system and emergency department simulation model"
        }
    };

    function setText(element, value) {
        if (element) element.textContent = value;
    }

    function setLanguage(language) {
        const lang = language === "en" ? "en" : "es";
        const t = content[lang];

        document.documentElement.lang = lang;

        setText(document.querySelector(".brand-project"), t.project);

        const nav = Array.from(document.querySelectorAll(".nav a"));
        nav.slice(0, 4).forEach((a, i) => setText(a, t.nav[i]));

        setText(document.querySelector(".login-btn"), t.login);
        setText(document.querySelector(".eyebrow"), t.eyebrow);

        const title = document.querySelector("#hero-title");
        if (title) title.innerHTML = t.title.join("<br>");

        setText(document.querySelector(".hero-lead"), t.lead);

        const heroButtons = Array.from(document.querySelectorAll(".hero-actions .btn"));
        setText(heroButtons[0], t.explore);
        setText(heroButtons[1], t.review);

        const quote = document.querySelector(".hero-quote");
        if (quote) quote.innerHTML = t.quote.join("<br>");

        if (banner) {
            banner.src = t.banner;
            banner.alt = t.bannerAlt;
        }

        buttons.forEach(button => {
            const active = button.dataset.siteLang === lang;
            button.classList.toggle("active", active);
            button.setAttribute("aria-pressed", active ? "true" : "false");
        });

        localStorage.setItem(KEY, lang);
    }

    buttons.forEach(button => {
        button.addEventListener("click", function () {
            setLanguage(this.dataset.siteLang);
        });
    });

    setLanguage(localStorage.getItem(KEY) || "es");
})();

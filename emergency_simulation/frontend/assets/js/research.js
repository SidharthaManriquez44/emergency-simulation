(function () {
    "use strict";

    const KEY = "sidhartha-language";
    const buttons = Array.from(document.querySelectorAll("[data-lang]"));

    function applyLanguage(language) {
        const lang = language === "en" ? "en" : "es";

        document.documentElement.lang = lang;
        document.documentElement.dataset.language = lang;

        buttons.forEach(button => {
            const active = button.dataset.lang === lang;

            button.classList.toggle("active", active);

            button.setAttribute(
                "aria-pressed",
                active ? "true" : "false"
            );
        });

        // =====================================================
        // Reader content
        // =====================================================

        document.querySelectorAll(".copy-es").forEach(el => {
            el.style.display = lang === "es" ? "" : "none";
        });

        document.querySelectorAll(".copy-en").forEach(el => {
            el.style.display = lang === "en" ? "" : "none";
        });

        // =====================================================
        // Sidebar labels
        // =====================================================

        document.querySelectorAll(".label-es").forEach(el => {
            el.style.display = lang === "es" ? "" : "none";
        });

        document.querySelectorAll(".label-en").forEach(el => {
            el.style.display = lang === "en" ? "" : "none";
        });

        localStorage.setItem(KEY, lang);
    }


// =========================================================
// Language switch
// =========================================================

buttons.forEach(button => {
    button.addEventListener("click", event => {
        event.preventDefault();
        event.stopPropagation();

        /*
         * Identificar la sección principal actual.
         * Ahora Metodología sí pertenece a .section.
         */
        const currentSection = sections
            .filter(section => {
                const rect = section.getBoundingClientRect();
                const sectionTop =
                    rect.top + window.scrollY;

                return sectionTop <= window.scrollY + 120;
            })
            .sort((a, b) => {
                const aTop =
                    a.getBoundingClientRect().top +
                    window.scrollY;

                const bTop =
                    b.getBoundingClientRect().top +
                    window.scrollY;

                return bTop - aTop;
            })[0];

        /*
         * Si por alguna razón no encontramos sección,
         * solamente cambiamos el idioma.
         */
        if (!currentSection) {
            applyLanguage(button.dataset.lang);
            return;
        }

        /*
         * Guardamos la posición relativa dentro de
         * la sección actual.
         */
        const sectionTopBefore =
            currentSection.getBoundingClientRect().top +
            window.scrollY;

        const offsetInsideSection =
            window.scrollY - sectionTopBefore;

        /*
         * Cambiar idioma.
         */
        applyLanguage(button.dataset.lang);

        /*
         * Esperamos a que el navegador recalcule
         * el nuevo layout.
         */
        requestAnimationFrame(() => {

            requestAnimationFrame(() => {

                const sectionTopAfter =
                    currentSection.getBoundingClientRect().top +
                    window.scrollY;

                /*
                 * Restaurar exactamente la misma posición
                 * relativa dentro de la sección.
                 */
                window.scrollTo({
                    top:
                        sectionTopAfter +
                        offsetInsideSection,
                    behavior: "auto"
                });

            });

        });
    });
});

    // Initial language
    applyLanguage(localStorage.getItem(KEY) || "es");

})();

// =============================================================
// TABLE OF CONTENTS / SECTION OBSERVER
// =============================================================

const links = [
    ...document.querySelectorAll(".toc a")
];

const sections = [
    ...document.querySelectorAll(".section")
];


// -------------------------------------------------------------
// Active state
// -------------------------------------------------------------

function setActiveLink(sectionId) {
    links.forEach(link => {
        const href = link.getAttribute("href");

        link.classList.toggle(
            "active",
            href === `#${sectionId}`
        );
    });
}


// -------------------------------------------------------------
// Click behavior
// -------------------------------------------------------------

links.forEach(link => {

    link.addEventListener("click", () => {

        const href = link.getAttribute("href");

        if (!href || !href.startsWith("#")) {
            return;
        }

        const sectionId = href.substring(1);

        setActiveLink(sectionId);
    });

});


// -------------------------------------------------------------
// Section observer
// -------------------------------------------------------------

const observer = new IntersectionObserver(
    entries => {

        const visibleSections = entries
            .filter(entry => entry.isIntersecting)
            .sort(
                (a, b) =>
                    b.intersectionRatio - a.intersectionRatio
            );

        if (!visibleSections.length) {
            return;
        }

        const visibleSection =
            visibleSections[0].target;

        setActiveLink(visibleSection.id);
    },
    {
        rootMargin: "-15% 0px -65% 0px",
        threshold: [0, 0.25, 0.5, 1]
    }
);


sections.forEach(section => {
    observer.observe(section);
});


// =============================================================
// SEARCH
// =============================================================

const panel = document.querySelector(".search-panel");
const searchButton = document.querySelector(".search-button");
const input = document.querySelector(".search-input");
const results = document.querySelector(".search-results");

searchButton?.addEventListener("click", () => {

    panel.classList.toggle("open");

    if (panel.classList.contains("open")) {
        input.focus();
    }
});

input?.addEventListener("input", () => {

    const q = input.value.trim().toLowerCase();

    results.innerHTML = "";

    if (q.length < 2) return;

    sections
        .map(section => ({
            id: section.id,
            title:
                section.querySelector("h1,h2")?.textContent || "",
            text:
                section.textContent
                    .replace(/\s+/g, " ")
                    .trim()
        }))
        .filter(item =>
            item.text.toLowerCase().includes(q)
        )
        .slice(0, 8)
        .forEach(item => {

            const a = document.createElement("a");

            a.className = "search-result";

            a.href = `#${item.id}`;

            a.innerHTML =
                `<strong>${item.title}</strong><br>` +
                `${item.text.slice(0, 170)}…`;

            a.addEventListener("click", () => {
                panel.classList.remove("open");
            });

            results.appendChild(a);
        });
});

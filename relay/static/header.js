(function () {
    function initHeader(header) {
        if (!header) {
            return;
        }
        const toggle = header.querySelector('.menu-toggle');
        const nav = header.querySelector('.mypage-nav');
        if (!toggle || !nav) {
            return;
        }
        const links = nav.querySelectorAll('a');
        const closeMenu = () => {
            toggle.setAttribute('aria-expanded', 'false');
            nav.classList.remove('open');
            header.classList.remove('menu-open');
        };
        toggle.addEventListener('click', function () {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', String(!isExpanded));
            nav.classList.toggle('open', !isExpanded);
            header.classList.toggle('menu-open', !isExpanded);
        });
        links.forEach((link) => {
            link.addEventListener('click', () => {
                if (window.matchMedia('(max-width: 768px)').matches) {
                    closeMenu();
                }
            });
        });
        document.addEventListener('click', (event) => {
            if (!header.contains(event.target)) {
                closeMenu();
            }
        });
        window.addEventListener('resize', () => {
            if (!window.matchMedia('(max-width: 820px)').matches) {
                closeMenu();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('.header').forEach(initHeader);
        });
    } else {
        document.querySelectorAll('.header').forEach(initHeader);
    }
})();

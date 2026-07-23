document.addEventListener('DOMContentLoaded', () => {
    const shell = document.querySelector('.app-shell');
    const toggle = document.querySelector('[data-sidebar-toggle]');
    if (shell && toggle) {
        toggle.addEventListener('click', () => {
            const collapsed = shell.classList.toggle('sidebar-collapsed');
            toggle.setAttribute('aria-expanded', String(!collapsed));
        });
    }
});

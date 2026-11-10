/**
 * Main Vue 3 Application Mount
 * Mounts Vue application, integrates Vue Router, and registers global components.
 */

document.addEventListener('DOMContentLoaded', () => {
    const { createApp } = Vue;

    const app = createApp({
        components: {
            'navbar-component': window.NavbarComponent,
            'toast-component': window.ToastComponent
        },
        template: `
        <div id="tma-app-root" class="d-flex flex-column min-vh-100">
            <!-- Global Floating Toast Notification Alerts -->
            <toast-component />

            <!-- Dynamic Role-Aware Navigation Bar -->
            <navbar-component />

            <!-- Main Route Outlet -->
            <main class="flex-grow-1">
                <router-view />
            </main>

            <!-- Sticky / Bottom Footer -->
            <footer class="bg-dark text-white-50 py-3 mt-auto border-top border-secondary">
                <div class="container text-center small">
                    <div class="mb-1">
                        <span class="text-white fw-semibold">Trekking Management Application (TMA)</span>
                        — MAD-2 University Project
                    </div>
                    <div class="text-muted">
                        Flask REST API &bull; SQLite &bull; Redis Caching &bull; Celery Workers &bull; Vue.js 3 &bull; Bootstrap 5
                    </div>
                </div>
            </footer>
        </div>
        `
    });

    if (window.router) {
        app.use(window.router);
    }

    app.mount('#app');
    console.log("TMA Vue 3 Single Page Application mounted successfully.");
});


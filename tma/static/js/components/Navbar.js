/**
 * Navbar Component
 * Dynamic header displaying role-aware navigation links, active badges, and user profile/logout actions.
 */

const Navbar = {
    name: 'Navbar',
    data() {
        const auth = window.tmaApi ? window.tmaApi.auth : null;
        return {
            token: auth ? auth.token : localStorage.getItem('tma_token'),
            role: auth ? auth.role : localStorage.getItem('tma_role'),
            user: auth ? auth.user : JSON.parse(localStorage.getItem('tma_user') || 'null'),
            unreadNotificationsCount: 0,
            notifications: [],
            showNotifModal: false,
            pollTimer: null
        };
    },
    computed: {
        isLoggedIn() {
            return !!this.token;
        },
        userRole() {
            return this.role || '';
        },
        userName() {
            if (this.user && this.user.name) return this.user.name;
            if (this.userRole === 'admin') return 'Administrator';
            if (this.userRole === 'staff') return 'Staff Guide';
            return 'User';
        }
    },
    watch: {
        $route() {
            this.syncAuth();
        }
    },
    methods: {
        syncAuth() {
            if (window.tmaApi && window.tmaApi.auth) {
                this.token = window.tmaApi.auth.token;
                this.role = window.tmaApi.auth.role;
                this.user = window.tmaApi.auth.user;
            } else {
                this.token = localStorage.getItem('tma_token');
                this.role = localStorage.getItem('tma_role');
                this.user = JSON.parse(localStorage.getItem('tma_user') || 'null');
            }

            if (this.isLoggedIn && this.userRole === 'user') {
                this.fetchNotifications();
            } else {
                this.notifications = [];
                this.unreadNotificationsCount = 0;
            }
        },
        logout() {
            if (window.tmaApi && window.tmaApi.auth) {
                window.tmaApi.auth.clearAuth();
            } else {
                localStorage.removeItem('tma_token');
                localStorage.removeItem('tma_role');
                localStorage.removeItem('tma_user');
            }
            if (this.pollTimer) clearInterval(this.pollTimer);
            this.syncAuth();
            if (window.showToast) {
                window.showToast("Signed out successfully.", "info");
            }
            this.$router.push('/login');
        },
        async fetchNotifications() {
            if (this.isLoggedIn && this.userRole === 'user') {
                try {
                    const res = await window.tmaApi.get('/user/notifications');
                    if (res && res.data) {
                        this.notifications = res.data.notifications || [];
                        this.unreadNotificationsCount = res.data.unread_count || 0;
                    }
                } catch (e) {
                    // Suppress polling error in background
                }
            }
        },
        async openNotifications() {
            await this.fetchNotifications();
            this.showNotifModal = true;
        },
        async markAllNotificationsRead() {
            try {
                await window.tmaApi.post('/user/notifications/read');
                this.unreadNotificationsCount = 0;
                this.notifications.forEach(n => n.is_read = true);
            } catch (e) {
                console.error("Failed to mark notifications read:", e);
            }
        }
    },
    mounted() {
        this.syncAuth();

        if (window.tmaApi && window.tmaApi.auth && typeof window.tmaApi.auth.subscribe === 'function') {
            window.tmaApi.auth.subscribe(() => {
                this.syncAuth();
            });
        }

        window.addEventListener('tma-auth-changed', () => {
            this.syncAuth();
        });

        window.addEventListener('storage', () => {
            this.syncAuth();
        });

        // Periodically poll for notifications if logged in as user
        this.pollTimer = setInterval(() => {
            if (this.isLoggedIn && this.userRole === 'user') {
                this.fetchNotifications();
            }
        }, 15000);
    },
    beforeUnmount() {
        if (this.pollTimer) clearInterval(this.pollTimer);
    },
    template: `
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow sticky-top">
        <div class="container">
            <router-link to="/treks" class="navbar-brand d-flex align-items-center gap-2 fw-bold fs-4">
                <i class="bi bi-compass-fill text-warning"></i>
                <span class="text-white">TMA <span class="text-warning">Treks</span></span>
            </router-link>

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent" aria-controls="navbarContent" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarContent">
                <!-- Left Nav Items -->
                <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                    <li v-if="isLoggedIn && userRole === 'user'" class="nav-item">
                        <router-link to="/dashboard" class="nav-link" active-class="active">
                            <i class="bi bi-speedometer2 me-1"></i>Dashboard
                        </router-link>
                    </li>
                    <li class="nav-item">
                        <router-link to="/treks" class="nav-link" active-class="active">
                            <i class="bi bi-map me-1"></i>Explore Treks
                        </router-link>
                    </li>
                    <li v-if="isLoggedIn && userRole === 'user'" class="nav-item">
                        <router-link to="/my-bookings" class="nav-link" active-class="active">
                            <i class="bi bi-journal-bookmark me-1"></i>My Bookings
                        </router-link>
                    </li>
                    <li v-if="isLoggedIn && userRole === 'staff'" class="nav-item">
                        <router-link to="/staff" class="nav-link" active-class="active">
                            <i class="bi bi-person-workspace me-1"></i>Staff Dashboard
                        </router-link>
                    </li>
                    <li v-if="isLoggedIn && userRole === 'admin'" class="nav-item">
                        <router-link to="/admin" class="nav-link" active-class="active">
                            <i class="bi bi-shield-shaded me-1"></i>Admin Control Panel
                        </router-link>
                    </li>
                </ul>

                <!-- Right Nav Items -->
                <div class="d-flex align-items-center gap-2">
                    <!-- LOGGED IN USER ACTIONS -->
                    <template v-if="isLoggedIn">
                        <!-- Notification Bell for Trekker Users -->
                        <button v-if="userRole === 'user'" 
                                @click="openNotifications" 
                                class="btn btn-outline-light position-relative me-1 btn-sm" 
                                title="View Notifications">
                            <i class="bi bi-bell-fill"></i>
                            <span v-if="unreadNotificationsCount > 0" 
                                  class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                                {{ unreadNotificationsCount }}
                            </span>
                        </button>

                        <!-- Profile Icon Link -->
                        <router-link to="/profile" class="btn btn-outline-light btn-sm d-flex align-items-center gap-2" title="My Profile">
                            <i class="bi bi-person-circle fs-5"></i>
                            <span class="d-none d-md-inline small fw-medium">{{ userName }}</span>
                        </router-link>

                        <!-- Settings Icon & Options Dropdown -->
                        <div class="dropdown">
                            <button class="btn btn-secondary dropdown-toggle btn-sm d-flex align-items-center gap-1 shadow-sm" 
                                    type="button" id="navbarSettingsMenu" data-bs-toggle="dropdown" aria-expanded="false" title="Account Settings & Menu">
                                <i class="bi bi-gear-fill"></i>
                                <span class="badge bg-warning text-dark text-capitalize ms-1">{{ userRole }}</span>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end shadow border-0" aria-labelledby="navbarSettingsMenu">
                                <li class="dropdown-header text-uppercase small fw-bold text-muted">
                                    Signed in as <strong class="text-dark">{{ userName }}</strong>
                                </li>
                                <li><hr class="dropdown-divider"></li>
                                <li>
                                    <router-link to="/profile" class="dropdown-item d-flex align-items-center gap-2">
                                        <i class="bi bi-person-gear text-primary"></i> Profile Settings
                                    </router-link>
                                </li>
                                <li v-if="userRole === 'admin'">
                                    <router-link to="/admin" class="dropdown-item d-flex align-items-center gap-2">
                                        <i class="bi bi-shield-shaded text-info"></i> Admin Control Panel
                                    </router-link>
                                </li>
                                <li v-if="userRole === 'staff'">
                                    <router-link to="/staff" class="dropdown-item d-flex align-items-center gap-2">
                                        <i class="bi bi-person-workspace text-info"></i> Staff Dashboard
                                    </router-link>
                                </li>
                                <li v-if="userRole === 'user'">
                                    <router-link to="/my-bookings" class="dropdown-item d-flex align-items-center gap-2">
                                        <i class="bi bi-journal-bookmark text-info"></i> My Bookings
                                    </router-link>
                                </li>
                                <li><hr class="dropdown-divider"></li>
                                <li>
                                    <button @click="logout" class="dropdown-item text-danger d-flex align-items-center gap-2">
                                        <i class="bi bi-box-arrow-right"></i> Logout
                                    </button>
                                </li>
                            </ul>
                        </div>
                    </template>

                    <!-- LOGGED OUT ACTIONS (Only shown when user is NOT logged in) -->
                    <template v-else>
                        <div class="d-flex gap-2">
                            <router-link to="/login" class="btn btn-outline-light btn-sm d-flex align-items-center gap-1">
                                <i class="bi bi-box-arrow-in-right"></i>
                                <span>Login</span>
                            </router-link>
                            <router-link to="/register" class="btn btn-warning btn-sm text-dark fw-semibold d-flex align-items-center gap-1">
                                <i class="bi bi-person-plus"></i>
                                <span>Register</span>
                            </router-link>
                        </div>
                    </template>
                </div>
            </div>
        </div>
    </nav>

    <!-- In-App Notifications Modal -->
    <div v-if="showNotifModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
        <div class="modal-dialog modal-dialog-scrollable">
            <div class="modal-content shadow-lg border-0">
                <div class="modal-header bg-dark text-white">
                    <h5 class="modal-title d-flex align-items-center gap-2">
                        <i class="bi bi-bell-fill text-warning"></i> Notifications
                    </h5>
                    <button type="button" class="btn-close btn-close-white" @click="showNotifModal = false"></button>
                </div>
                <div class="modal-body p-0">
                    <div class="p-2 border-bottom d-flex justify-content-between align-items-center bg-light">
                        <span class="text-muted small">{{ notifications.length }} notifications total</span>
                        <button v-if="unreadNotificationsCount > 0" 
                                @click="markAllNotificationsRead" 
                                class="btn btn-link btn-sm text-decoration-none p-0">
                            Mark all as read
                        </button>
                    </div>
                    <div v-if="notifications.length === 0" class="text-center p-4 text-muted">
                        <i class="bi bi-bell-slash fs-2 d-block mb-2"></i>
                        No notifications yet.
                    </div>
                    <ul v-else class="list-group list-group-flush">
                        <li v-for="n in notifications" :key="n.id" 
                            class="list-group-item" 
                            :class="{'bg-light font-weight-bold': !n.is_read}">
                            <div class="d-flex justify-content-between">
                                <small class="text-muted">{{ n.created_at ? n.created_at.substring(0, 16) : '' }}</small>
                                <span v-if="!n.is_read" class="badge bg-primary">New</span>
                            </div>
                            <div class="mt-1" style="font-size: 0.9rem;">
                                {{ n.message }}
                            </div>
                        </li>
                    </ul>
                </div>
                <div class="modal-footer bg-light p-2">
                    <button type="button" class="btn btn-secondary btn-sm" @click="showNotifModal = false">Close</button>
                </div>
            </div>
        </div>
    </div>
    `
};

window.NavbarComponent = Navbar;

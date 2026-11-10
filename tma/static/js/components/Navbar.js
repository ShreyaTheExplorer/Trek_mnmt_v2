/**
 * Navbar Component
 * Dynamic header displaying role-aware navigation links, active badges, and user profile/logout actions.
 */

const Navbar = {
    name: 'Navbar',
    data() {
        return {
            auth: window.tmaApi.auth,
            unreadNotificationsCount: 0,
            notifications: [],
            showNotifModal: false,
            pollTimer: null
        };
    },
    computed: {
        isLoggedIn() {
            return this.auth.isAuthenticated();
        },
        userRole() {
            return this.auth.role;
        },
        userName() {
            return this.auth.user ? this.auth.user.name : 'User';
        }
    },
    methods: {
        logout() {
            window.tmaApi.auth.clearAuth();
            if (this.pollTimer) clearInterval(this.pollTimer);
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
        this.fetchNotifications();
        // Periodically poll for notifications if logged in as user
        this.pollTimer = setInterval(() => {
            this.fetchNotifications();
        }, 15000);

        window.tmaApi.auth.subscribe(() => {
            this.fetchNotifications();
        });
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

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarContent">
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

                <div class="d-flex align-items-center gap-2">
                    <!-- Notification Bell for Trekker Users -->
                    <button v-if="isLoggedIn && userRole === 'user'" 
                            @click="openNotifications" 
                            class="btn btn-outline-light position-relative me-2 btn-sm" 
                            title="View Notifications">
                        <i class="bi bi-bell-fill"></i>
                        <span v-if="unreadNotificationsCount > 0" 
                              class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                            {{ unreadNotificationsCount }}
                        </span>
                    </button>

                    <!-- User Dropdown when Logged In -->
                    <div v-if="isLoggedIn" class="dropdown">
                        <button class="btn btn-secondary dropdown-toggle btn-sm d-flex align-items-center gap-2" 
                                type="button" data-bs-toggle="dropdown">
                            <i class="bi bi-person-circle"></i>
                            <span>{{ userName }}</span>
                            <span class="badge bg-warning text-dark text-capitalize ms-1">{{ userRole }}</span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end shadow">
                            <li>
                                <router-link to="/profile" class="dropdown-item">
                                    <i class="bi bi-person-gear me-2"></i>My Profile
                                </router-link>
                            </li>
                            <li><hr class="dropdown-divider"></li>
                            <li>
                                <button @click="logout" class="dropdown-item text-danger">
                                    <i class="bi bi-box-arrow-right me-2"></i>Sign Out
                                </button>
                            </li>
                        </ul>
                    </div>

                    <!-- Auth buttons when Logged Out -->
                    <div v-else class="d-flex gap-2">
                        <router-link to="/login" class="btn btn-outline-light btn-sm">
                            <i class="bi bi-box-arrow-in-right me-1"></i>Login
                        </router-link>
                        <router-link to="/register" class="btn btn-warning btn-sm text-dark fw-semibold">
                            <i class="bi bi-person-plus me-1"></i>Register
                        </router-link>
                    </div>
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


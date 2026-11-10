/**
 * AdminView Component
 * Top-level responsive navigation hub wrapping all administrative modules.
 */

const AdminView = {
    name: 'AdminView',
    components: {
        'admin-dashboard': window.AdminDashboard,
        'admin-treks': window.AdminTreks,
        'admin-staff': window.AdminStaff,
        'admin-users': window.AdminUsers,
        'admin-bookings': window.AdminBookings,
        'admin-search': window.AdminSearch
    },
    data() {
        return {
            activeTab: 'dashboard'
        };
    },
    watch: {
        '$route.params.tab': {
            immediate: true,
            handler(tab) {
                if (tab && ['dashboard', 'treks', 'staff', 'users', 'bookings', 'search'].includes(tab)) {
                    this.activeTab = tab;
                } else {
                    this.activeTab = 'dashboard';
                }
            }
        }
    },
    methods: {
        switchTab(tab) {
            this.activeTab = tab;
            this.$router.push(`/admin/${tab}`);
        }
    },
    template: `
    <div class="bg-light flex-grow-1">
        <!-- Sub-navigation Bar -->
        <div class="bg-white border-bottom shadow-sm">
            <div class="container-fluid">
                <ul class="nav nav-pills flex-nowrap overflow-auto py-2 gap-1">
                    <li class="nav-item">
                        <button class="nav-link py-2 px-3 d-flex align-items-center gap-2" 
                                :class="{ 'active': activeTab === 'dashboard' }" 
                                @click="switchTab('dashboard')">
                            <i class="bi bi-speedometer2"></i>
                            <span>Dashboard</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button class="nav-link py-2 px-3 d-flex align-items-center gap-2" 
                                :class="{ 'active': activeTab === 'treks' }" 
                                @click="switchTab('treks')">
                            <i class="bi bi-compass"></i>
                            <span>Treks Management</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button class="nav-link py-2 px-3 d-flex align-items-center gap-2" 
                                :class="{ 'active': activeTab === 'staff' }" 
                                @click="switchTab('staff')">
                            <i class="bi bi-person-workspace"></i>
                            <span>Staff & Guides</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button class="nav-link py-2 px-3 d-flex align-items-center gap-2" 
                                :class="{ 'active': activeTab === 'users' }" 
                                @click="switchTab('users')">
                            <i class="bi bi-people"></i>
                            <span>Trekker Users</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button class="nav-link py-2 px-3 d-flex align-items-center gap-2" 
                                :class="{ 'active': activeTab === 'bookings' }" 
                                @click="switchTab('bookings')">
                            <i class="bi bi-journal-bookmark"></i>
                            <span>Bookings Ledger</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button class="nav-link py-2 px-3 d-flex align-items-center gap-2" 
                                :class="{ 'active': activeTab === 'search' }" 
                                @click="switchTab('search')">
                            <i class="bi bi-search"></i>
                            <span>Global Search</span>
                        </button>
                    </li>
                </ul>
            </div>
        </div>

        <!-- Render Current Active Sub-component -->
        <main>
            <admin-dashboard v-if="activeTab === 'dashboard'" />
            <admin-treks v-else-if="activeTab === 'treks'" />
            <admin-staff v-else-if="activeTab === 'staff'" />
            <admin-users v-else-if="activeTab === 'users'" />
            <admin-bookings v-else-if="activeTab === 'bookings'" />
            <admin-search v-else-if="activeTab === 'search'" />
        </main>
    </div>
    `
};

window.AdminView = AdminView;


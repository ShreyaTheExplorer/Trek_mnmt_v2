/**
 * AdminUsers Component
 * Trekker directory, profile inspection, and account moderation controls.
 */

const AdminUsers = {
    name: 'AdminUsers',
    data() {
        return {
            users: [],
            loading: false,
            searchQuery: '',
            filterStatus: ''
        };
    },
    computed: {
        filteredUsers() {
            let list = this.users;
            if (this.searchQuery) {
                const q = this.searchQuery.toLowerCase();
                list = list.filter(u => 
                    (u.name && u.name.toLowerCase().includes(q)) || 
                    (u.email && u.email.toLowerCase().includes(q)) ||
                    (u.phone && u.phone.toLowerCase().includes(q))
                );
            }
            if (this.filterStatus) {
                list = list.filter(u => u.status === this.filterStatus);
            }
            return list;
        }
    },
    methods: {
        async fetchUsers() {
            this.loading = true;
            try {
                const params = {};
                if (this.searchQuery) params.q = this.searchQuery;
                if (this.filterStatus) params.status = this.filterStatus;

                const res = await window.tmaApi.get('/admin/users', params);
                if (res && res.data) {
                    this.users = res.data;
                }
            } catch (err) {
                window.showToast("Failed to fetch user directory: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        async setUserStatus(user, newStatus) {
            try {
                await window.tmaApi.patch(`/admin/users/${user.id}/status`, { status: newStatus });
                window.showToast(`User '${user.name}' status set to '${newStatus}'.`, "success");
                user.status = newStatus;
            } catch (err) {
                window.showToast("Failed to update user status: " + err.message, "danger");
            }
        }
    },
    mounted() {
        this.fetchUsers();
    },
    template: `
    <div class="container-fluid py-4">
        <!-- Title Banner -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-people-fill text-primary me-2"></i>Trekker User Directory
                </h3>
                <p class="text-muted small mb-0">Browse registered customer profiles and toggle account statuses (active, inactive, blacklisted).</p>
            </div>
            <button @click="fetchUsers" class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1">
                <i class="bi bi-arrow-clockwise"></i> Refresh List
            </button>
        </div>

        <!-- Filter & Search Controls Card -->
        <div class="card border-0 shadow-sm rounded-3 mb-4">
            <div class="card-body p-3">
                <div class="row g-2 align-items-center">
                    <div class="col-12 col-md-6 col-lg-5">
                        <div class="input-group">
                            <span class="input-group-text bg-light text-muted border-end-0">
                                <i class="bi bi-search"></i>
                            </span>
                            <input 
                                type="text" 
                                v-model="searchQuery" 
                                class="form-control border-start-0" 
                                placeholder="Search by name, email, or phone number..." 
                            />
                        </div>
                    </div>
                    <div class="col-6 col-md-3 col-lg-3">
                        <select v-model="filterStatus" class="form-select">
                            <option value="">All Statuses</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="blacklisted">Blacklisted</option>
                        </select>
                    </div>
                    <div class="col-6 col-md-3 col-lg-4 text-end text-muted small">
                        Showing <strong>{{ filteredUsers.length }}</strong> trekkers
                    </div>
                </div>
            </div>
        </div>

        <!-- Responsive Users Table Card -->
        <div class="card border-0 shadow-sm rounded-3 overflow-hidden">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light text-secondary text-uppercase small">
                        <tr>
                            <th style="width: 50px;">ID</th>
                            <th>Trekker Name</th>
                            <th>Contact Phone</th>
                            <th>Age</th>
                            <th>Emergency Contact</th>
                            <th>Residential Address</th>
                            <th>Account Status</th>
                            <th class="text-end">Account Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="loading">
                            <td colspan="8" class="text-center py-5 text-muted">
                                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                                Loading user accounts...
                            </td>
                        </tr>
                        <tr v-else-if="filteredUsers.length === 0">
                            <td colspan="8" class="text-center py-5 text-muted">
                                <i class="bi bi-person-x fs-2 d-block mb-2"></i>
                                No user accounts matching the criteria.
                            </td>
                        </tr>
                        <tr v-for="user in filteredUsers" :key="user.id">
                            <td class="fw-bold text-muted">#{{ user.id }}</td>
                            <td>
                                <div class="fw-bold text-dark">{{ user.name }}</div>
                                <small class="text-muted">{{ user.email }}</small>
                            </td>
                            <td class="small">{{ user.phone || 'N/A' }}</td>
                            <td class="small">{{ user.age || '-' }}</td>
                            <td class="small text-muted">{{ user.emergency_contact || '-' }}</td>
                            <td class="small text-muted">{{ user.address || '-' }}</td>
                            <td>
                                <span class="badge" 
                                      :class="{
                                          'bg-success': user.status === 'active',
                                          'bg-warning text-dark': user.status === 'inactive',
                                          'bg-danger': user.status === 'blacklisted'
                                      }">
                                    {{ user.status }}
                                </span>
                            </td>
                            <td class="text-end">
                                <div class="btn-group btn-group-sm">
                                    <button v-if="user.status !== 'active'" 
                                            @click="setUserStatus(user, 'active')" 
                                            class="btn btn-outline-success" 
                                            title="Activate Account">
                                        <i class="bi bi-check-circle me-1"></i>Activate
                                    </button>
                                    <button v-if="user.status === 'active'" 
                                            @click="setUserStatus(user, 'inactive')" 
                                            class="btn btn-outline-warning" 
                                            title="Deactivate Account">
                                        <i class="bi bi-pause-circle me-1"></i>Deactivate
                                    </button>
                                    <button v-if="user.status !== 'blacklisted'" 
                                            @click="setUserStatus(user, 'blacklisted')" 
                                            class="btn btn-outline-danger" 
                                            title="Blacklist Account">
                                        <i class="bi bi-slash-circle me-1"></i>Blacklist
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `
};

window.AdminUsers = AdminUsers;


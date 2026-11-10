/**
 * AdminStaff Component
 * Staff onboarding, specialized role assignments, and lifecycle status management.
 */

const AdminStaff = {
    name: 'AdminStaff',
    data() {
        return {
            staffMembers: [],
            loading: false,
            searchQuery: '',
            showAddModal: false,
            showEditModal: false,
            actionLoading: false,

            staffForm: {
                name: '',
                email: '',
                password: '',
                phone: '',
                specialization: '',
                contact_details: ''
            },
            currentEditStaff: null
        };
    },
    computed: {
        filteredStaff() {
            if (!this.searchQuery) return this.staffMembers;
            const q = this.searchQuery.toLowerCase();
            return this.staffMembers.filter(s => 
                (s.name && s.name.toLowerCase().includes(q)) || 
                (s.email && s.email.toLowerCase().includes(q)) ||
                (s.specialization && s.specialization.toLowerCase().includes(q))
            );
        }
    },
    methods: {
        async fetchStaff() {
            this.loading = true;
            try {
                const params = this.searchQuery ? { q: this.searchQuery } : {};
                const res = await window.tmaApi.get('/admin/staff', params);
                if (res && res.data) {
                    this.staffMembers = res.data;
                }
            } catch (err) {
                window.showToast("Failed to fetch staff members: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        openAddModal() {
            this.staffForm = {
                name: '',
                email: '',
                password: '',
                phone: '',
                specialization: 'High-Altitude Guide',
                contact_details: ''
            };
            this.showAddModal = true;
        },

        async createStaff() {
            if (!this.staffForm.name || !this.staffForm.email || !this.staffForm.password || !this.staffForm.phone) {
                window.showToast("Please complete all required fields.", "warning");
                return;
            }
            this.actionLoading = true;
            try {
                await window.tmaApi.post('/admin/staff', this.staffForm);
                window.showToast("Staff member onboarded successfully!", "success");
                this.showAddModal = false;
                await this.fetchStaff();
            } catch (err) {
                window.showToast("Failed to create staff: " + err.message, "danger");
            } finally {
                this.actionLoading = false;
            }
        },

        openEditModal(staff) {
            this.currentEditStaff = staff;
            this.staffForm = {
                name: staff.name,
                phone: staff.phone || '',
                specialization: staff.specialization || '',
                contact_details: staff.contact_details || '',
                password: ''
            };
            this.showEditModal = true;
        },

        async updateStaff() {
            if (!this.currentEditStaff) return;
            this.actionLoading = true;
            try {
                const payload = {
                    name: this.staffForm.name,
                    phone: this.staffForm.phone,
                    specialization: this.staffForm.specialization,
                    contact_details: this.staffForm.contact_details
                };
                if (this.staffForm.password) {
                    payload.password = this.staffForm.password;
                }
                await window.tmaApi.put(`/admin/staff/${this.currentEditStaff.id}`, payload);
                window.showToast("Staff profile updated successfully!", "success");
                this.showEditModal = false;
                await this.fetchStaff();
            } catch (err) {
                window.showToast("Failed to update staff: " + err.message, "danger");
            } finally {
                this.actionLoading = false;
            }
        },

        async setStaffStatus(staff, newStatus) {
            try {
                await window.tmaApi.patch(`/admin/staff/${staff.id}/status`, { status: newStatus });
                window.showToast(`Staff member status updated to '${newStatus}'.`, "success");
                staff.status = newStatus;
            } catch (err) {
                window.showToast("Status change failed: " + err.message, "danger");
            }
        }
    },
    mounted() {
        this.fetchStaff();
    },
    template: `
    <div class="container-fluid py-4">
        <!-- Header & Add Button -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-person-workspace text-warning me-2"></i>Staff & Guide Directory
                </h3>
                <p class="text-muted small mb-0">Onboard coordinators, manage mountain guide credentials, and regulate active access.</p>
            </div>
            <button @click="openAddModal" class="btn btn-primary d-flex align-items-center gap-2 shadow-sm">
                <i class="bi bi-person-plus-fill"></i> Add Staff Member
            </button>
        </div>

        <!-- Search Bar Card -->
        <div class="card border-0 shadow-sm rounded-3 mb-4">
            <div class="card-body p-3">
                <div class="row g-2 align-items-center">
                    <div class="col-12 col-md-6 col-lg-4">
                        <div class="input-group">
                            <span class="input-group-text bg-light text-muted border-end-0">
                                <i class="bi bi-search"></i>
                            </span>
                            <input 
                                type="text" 
                                v-model="searchQuery" 
                                class="form-control border-start-0" 
                                placeholder="Search by name, email, or specialty..." 
                            />
                        </div>
                    </div>
                    <div class="col-6 col-md-3 col-lg-2">
                        <button @click="fetchStaff" class="btn btn-outline-secondary w-100">
                            <i class="bi bi-arrow-clockwise me-1"></i> Refresh
                        </button>
                    </div>
                    <div class="col-12 col-md-3 col-lg-6 text-md-end text-muted small">
                        Showing <strong>{{ filteredStaff.length }}</strong> staff members
                    </div>
                </div>
            </div>
        </div>

        <!-- Responsive Staff Table Card -->
        <div class="card border-0 shadow-sm rounded-3 overflow-hidden">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light text-secondary text-uppercase small">
                        <tr>
                            <th style="width: 50px;">ID</th>
                            <th>Staff Member</th>
                            <th>Contact & Emergency</th>
                            <th>Specialization</th>
                            <th>Joined On</th>
                            <th>Account Status</th>
                            <th class="text-end">Lifecycle Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="loading">
                            <td colspan="7" class="text-center py-5 text-muted">
                                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                                Loading staff records...
                            </td>
                        </tr>
                        <tr v-else-if="filteredStaff.length === 0">
                            <td colspan="7" class="text-center py-5 text-muted">
                                <i class="bi bi-person-x fs-2 d-block mb-2"></i>
                                No staff members found.
                            </td>
                        </tr>
                        <tr v-for="staff in filteredStaff" :key="staff.id">
                            <td class="fw-bold text-muted">#{{ staff.id }}</td>
                            <td>
                                <div class="fw-bold text-dark">{{ staff.name }}</div>
                                <small class="text-muted">{{ staff.email }}</small>
                            </td>
                            <td>
                                <div class="small fw-semibold">{{ staff.phone || 'N/A' }}</div>
                                <small class="text-muted">{{ staff.contact_details || 'No extra contacts' }}</small>
                            </td>
                            <td>
                                <span class="badge bg-secondary text-light">
                                    {{ staff.specialization || 'General Guide' }}
                                </span>
                            </td>
                            <td class="small text-muted">
                                {{ staff.joined_on ? staff.joined_on.substring(0, 10) : 'N/A' }}
                            </td>
                            <td>
                                <span class="badge" 
                                      :class="{
                                          'bg-success': staff.status === 'active',
                                          'bg-warning text-dark': staff.status === 'inactive',
                                          'bg-danger': staff.status === 'blacklisted'
                                      }">
                                    {{ staff.status }}
                                </span>
                            </td>
                            <td class="text-end">
                                <div class="btn-group btn-group-sm">
                                    <button @click="openEditModal(staff)" class="btn btn-outline-primary" title="Edit Profile">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button v-if="staff.status !== 'active'" 
                                            @click="setStaffStatus(staff, 'active')" 
                                            class="btn btn-outline-success" 
                                            title="Activate Account">
                                        <i class="bi bi-check-circle"></i>
                                    </button>
                                    <button v-if="staff.status === 'active'" 
                                            @click="setStaffStatus(staff, 'inactive')" 
                                            class="btn btn-outline-warning" 
                                            title="Deactivate Account">
                                        <i class="bi bi-pause-circle"></i>
                                    </button>
                                    <button v-if="staff.status !== 'blacklisted'" 
                                            @click="setStaffStatus(staff, 'blacklisted')" 
                                            class="btn btn-outline-danger" 
                                            title="Blacklist Account">
                                        <i class="bi bi-slash-circle"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Add Staff Modal -->
        <div v-if="showAddModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-dark text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-person-plus-fill text-warning me-2"></i>Onboard New Staff Member
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="showAddModal = false"></button>
                    </div>
                    <div class="modal-body">
                        <form @submit.prevent="createStaff">
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Staff Full Name *</label>
                                <input type="text" v-model="staffForm.name" class="form-control" placeholder="e.g. Tenzing Norgay" required />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Email Address *</label>
                                <input type="email" v-model="staffForm.email" class="form-control" placeholder="staff@tma.com" required />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Password *</label>
                                <input type="password" v-model="staffForm.password" class="form-control" minlength="6" placeholder="Minimum 6 characters" required />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Phone Number *</label>
                                <input type="tel" v-model="staffForm.phone" class="form-control" placeholder="+91 9876543210" required />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Specialization / Expertise</label>
                                <input type="text" v-model="staffForm.specialization" class="form-control" placeholder="e.g. Glacier Navigation, Wilderness First Aid" />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Basecamp / Emergency Contact Details</label>
                                <textarea v-model="staffForm.contact_details" class="form-control" rows="2" placeholder="Basecamp radio channel, emergency contacts..."></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" @click="showAddModal = false">Cancel</button>
                        <button type="button" class="btn btn-primary btn-sm" :disabled="actionLoading" @click="createStaff">
                            <span v-if="actionLoading" class="spinner-border spinner-border-sm me-1"></span>
                            Complete Onboarding
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Edit Staff Modal -->
        <div v-if="showEditModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-dark text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-pencil-square text-warning me-2"></i>Edit Staff #{{ currentEditStaff ? currentEditStaff.id : '' }}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="showEditModal = false"></button>
                    </div>
                    <div class="modal-body">
                        <form @submit.prevent="updateStaff">
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Name</label>
                                <input type="text" v-model="staffForm.name" class="form-control" required />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Phone Number</label>
                                <input type="tel" v-model="staffForm.phone" class="form-control" required />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Specialization</label>
                                <input type="text" v-model="staffForm.specialization" class="form-control" />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Contact Details</label>
                                <textarea v-model="staffForm.contact_details" class="form-control" rows="2"></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Reset Password (Optional)</label>
                                <input type="password" v-model="staffForm.password" class="form-control" placeholder="Leave blank to keep unchanged" />
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" @click="showEditModal = false">Cancel</button>
                        <button type="button" class="btn btn-primary btn-sm" :disabled="actionLoading" @click="updateStaff">
                            <span v-if="actionLoading" class="spinner-border spinner-border-sm me-1"></span>
                            Save Profile
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.AdminStaff = AdminStaff;


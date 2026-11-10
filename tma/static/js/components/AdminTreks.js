/**
 * AdminTreks Component
 * Complete CRUD management, staff assignment, date validation, and status controls for treks.
 */

const AdminTreks = {
    name: 'AdminTreks',
    data() {
        return {
            treks: [],
            staffList: [],
            loading: false,
            searchQuery: '',
            filterStatus: '',
            
            // Modal states
            showTrekModal: false,
            isEditing: false,
            currentTrekId: null,
            modalError: '',
            modalSuccess: '',
            dateErrors: {
                start_date: '',
                end_date: ''
            },
            fieldErrors: {},
            trekForm: {
                name: '',
                location: '',
                difficulty: 'Moderate',
                status: 'Open',
                duration_days: 3,
                total_slots: 20,
                start_date: '',
                end_date: '',
                price: 5000,
                description: '',
                instructions: ''
            },

            // Assign Staff Modal
            showAssignModal: false,
            assignTrek: null,
            selectedStaffId: '',

            // Delete Modal
            showDeleteModal: false,
            deleteTrekTarget: null,
            cancelActiveBookings: false,
            actionLoading: false
        };
    },
    computed: {
        filteredTreks() {
            let list = this.treks;
            if (this.searchQuery) {
                const q = this.searchQuery.toLowerCase();
                list = list.filter(t => 
                    (t.name && t.name.toLowerCase().includes(q)) || 
                    (t.location && t.location.toLowerCase().includes(q))
                );
            }
            if (this.filterStatus) {
                list = list.filter(t => t.status === this.filterStatus);
            }
            return list;
        }
    },
    methods: {
        async fetchTreks() {
            this.loading = true;
            try {
                const params = {};
                if (this.searchQuery) {
                    params.search = this.searchQuery;
                    params.q = this.searchQuery;
                }
                if (this.filterStatus) params.status = this.filterStatus;

                const res = await window.tmaApi.get('/admin/treks', params);
                if (res && res.data) {
                    this.treks = res.data;
                }
            } catch (err) {
                if (window.showToast) {
                    window.showToast("Failed to fetch treks: " + err.message, "danger");
                }
            } finally {
                this.loading = false;
            }
        },

        async fetchStaff() {
            try {
                const res = await window.tmaApi.get('/admin/staff');
                if (res && res.data) {
                    this.staffList = res.data.filter(s => s.status === 'active');
                }
            } catch (err) {
                console.error("Could not fetch staff for assignment:", err);
            }
        },

        formatDate(dateObj) {
            const year = dateObj.getFullYear();
            const month = String(dateObj.getMonth() + 1).padStart(2, '0');
            const day = String(dateObj.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        },

        openCreateModal() {
            this.isEditing = false;
            this.currentTrekId = null;
            this.modalError = '';
            this.modalSuccess = '';
            this.dateErrors = { start_date: '', end_date: '' };
            this.fieldErrors = {};

            const today = new Date();
            const defaultStart = new Date(today);
            defaultStart.setDate(today.getDate() + 7);
            const defaultEnd = new Date(today);
            defaultEnd.setDate(today.getDate() + 12);

            this.trekForm = {
                name: '',
                location: '',
                difficulty: 'Moderate',
                status: 'Open',
                duration_days: 5,
                total_slots: 20,
                start_date: this.formatDate(defaultStart),
                end_date: this.formatDate(defaultEnd),
                price: 5000,
                description: '',
                instructions: ''
            };
            this.showTrekModal = true;
        },

        openEditModal(trek) {
            this.isEditing = true;
            this.currentTrekId = trek.id;
            this.modalError = '';
            this.modalSuccess = '';
            this.dateErrors = { start_date: '', end_date: '' };
            this.fieldErrors = {};

            this.trekForm = {
                name: trek.name,
                location: trek.location,
                difficulty: trek.difficulty,
                status: trek.status || 'Pending',
                duration_days: trek.duration_days,
                total_slots: trek.total_slots,
                start_date: trek.start_date,
                end_date: trek.end_date,
                price: trek.price,
                description: trek.description,
                instructions: trek.instructions || ''
            };
            this.showTrekModal = true;
        },

        validateDates() {
            this.dateErrors = { start_date: '', end_date: '' };
            
            if (!this.trekForm.start_date) {
                this.dateErrors.start_date = "Start Date is required.";
                return false;
            }
            if (!this.trekForm.end_date) {
                this.dateErrors.end_date = "End Date is required.";
                return false;
            }

            // ISO YYYY-MM-DD string comparison
            if (this.trekForm.start_date > this.trekForm.end_date) {
                const msg = `Invalid Date Range: Start Date (${this.trekForm.start_date}) cannot be after End Date (${this.trekForm.end_date}). End Date must be greater than or equal to Start Date.`;
                this.dateErrors.start_date = `Start Date (${this.trekForm.start_date}) is after End Date (${this.trekForm.end_date}).`;
                this.dateErrors.end_date = `End Date (${this.trekForm.end_date}) cannot be earlier than Start Date (${this.trekForm.start_date}).`;
                this.modalError = msg;
                return false;
            }

            return true;
        },

        validateForm() {
            this.fieldErrors = {};
            this.modalError = '';
            let isValid = true;

            if (!this.trekForm.name || this.trekForm.name.trim().length < 3) {
                this.fieldErrors.name = "Trek name is required and must be at least 3 characters.";
                isValid = false;
            }

            if (!this.trekForm.location || !this.trekForm.location.trim()) {
                this.fieldErrors.location = "Location is required.";
                isValid = false;
            }

            if (!this.trekForm.description || this.trekForm.description.trim().length < 10) {
                this.fieldErrors.description = "Description is required and must be at least 10 characters.";
                isValid = false;
            }

            if (this.trekForm.duration_days == null || parseInt(this.trekForm.duration_days) < 1) {
                this.fieldErrors.duration_days = "Duration days must be a positive number (at least 1 day).";
                isValid = false;
            }

            if (this.trekForm.total_slots == null || parseInt(this.trekForm.total_slots) < 0) {
                this.fieldErrors.total_slots = "Total slots must be an integer greater than or equal to 0.";
                isValid = false;
            }

            if (this.trekForm.price == null || parseFloat(this.trekForm.price) < 0) {
                this.fieldErrors.price = "Price must be a non-negative number.";
                isValid = false;
            }

            if (!this.validateDates()) {
                isValid = false;
            }

            if (!isValid && !this.modalError) {
                const first = Object.values(this.fieldErrors)[0] || Object.values(this.dateErrors)[0];
                this.modalError = first || "Please complete all required fields correctly.";
            }

            return isValid;
        },

        async saveTrek() {
            this.modalError = '';
            this.modalSuccess = '';

            if (!this.validateForm()) {
                if (window.showToast) {
                    window.showToast(this.modalError, "danger");
                }
                return;
            }

            this.actionLoading = true;
            try {
                let res;
                if (this.isEditing) {
                    res = await window.tmaApi.put(`/admin/treks/${this.currentTrekId}`, this.trekForm);
                    const msg = (res && res.message) || "Trek details updated successfully!";
                    this.modalSuccess = msg;
                    if (window.showToast) window.showToast(msg, "success");
                } else {
                    res = await window.tmaApi.post('/admin/treks', this.trekForm);
                    const msg = (res && res.message) || "New trek created successfully!";
                    this.modalSuccess = msg;
                    if (window.showToast) window.showToast(msg, "success");
                }

                await this.fetchTreks();
                setTimeout(() => {
                    this.showTrekModal = false;
                    this.modalSuccess = '';
                }, 800);
            } catch (err) {
                const errMsg = err.message || (err.data && err.data.message) || "Failed to save trek.";
                this.modalError = errMsg;
                if (window.showToast) {
                    window.showToast("Failed to save trek: " + errMsg, "danger");
                }
            } finally {
                this.actionLoading = false;
            }
        },

        openAssignModal(trek) {
            this.assignTrek = trek;
            this.selectedStaffId = trek.assigned_staff ? trek.assigned_staff.id : '';
            this.fetchStaff();
            this.showAssignModal = true;
        },

        async submitAssignment() {
            if (!this.selectedStaffId) {
                window.showToast("Please select a staff member.", "warning");
                return;
            }
            this.actionLoading = true;
            try {
                await window.tmaApi.post(`/admin/treks/${this.assignTrek.id}/assign`, {
                    staff_id: parseInt(this.selectedStaffId)
                });
                window.showToast("Staff assigned successfully!", "success");
                this.showAssignModal = false;
                await this.fetchTreks();
            } catch (err) {
                window.showToast("Assignment failed: " + err.message, "danger");
            } finally {
                this.actionLoading = false;
            }
        },

        async updateTrekStatus(trek, newStatus) {
            try {
                await window.tmaApi.put(`/admin/treks/${trek.id}`, { status: newStatus });
                window.showToast(`Trek status changed to '${newStatus}'.`, "success");
                trek.status = newStatus;
            } catch (err) {
                window.showToast("Failed to update status: " + err.message, "danger");
            }
        },

        openDeleteModal(trek) {
            this.deleteTrekTarget = trek;
            this.cancelActiveBookings = false;
            this.showDeleteModal = true;
        },

        async confirmDelete() {
            if (!this.deleteTrekTarget) return;
            this.actionLoading = true;
            try {
                const path = `/admin/treks/${this.deleteTrekTarget.id}` + 
                    (this.cancelActiveBookings ? '?cancel_bookings=true' : '');
                await window.tmaApi.delete(path);
                window.showToast(`Trek '${this.deleteTrekTarget.name}' deleted successfully.`, "success");
                this.showDeleteModal = false;
                await this.fetchTreks();
            } catch (err) {
                window.showToast("Cannot delete trek: " + err.message, "danger");
            } finally {
                this.actionLoading = false;
            }
        }
    },
    mounted() {
        this.fetchTreks();
        this.fetchStaff();
    },
    template: `
    <div class="container-fluid py-4">
        <!-- Header & Action Row -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-compass text-primary me-2"></i>Trek Management
                </h3>
                <p class="text-muted small mb-0">Create, configure, assign staff, and manage operational statuses for all treks.</p>
            </div>
            <button @click="openCreateModal" class="btn btn-primary d-flex align-items-center gap-2 shadow-sm">
                <i class="bi bi-plus-circle-fill"></i> Add New Trek
            </button>
        </div>

        <!-- Filter & Search Controls Card -->
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
                                placeholder="Search by trek name or location..." 
                            />
                        </div>
                    </div>
                    <div class="col-6 col-md-3 col-lg-3">
                        <select v-model="filterStatus" class="form-select">
                            <option value="">All Statuses</option>
                            <option value="Pending">Pending</option>
                            <option value="Approved">Approved</option>
                            <option value="Open">Open</option>
                            <option value="Closed">Closed</option>
                            <option value="Completed">Completed</option>
                        </select>
                    </div>
                    <div class="col-6 col-md-3 col-lg-2">
                        <button @click="fetchTreks" class="btn btn-outline-secondary w-100">
                            <i class="bi bi-arrow-clockwise me-1"></i> Refresh
                        </button>
                    </div>
                    <div class="col-12 col-lg-3 text-lg-end text-muted small">
                        Showing <strong>{{ filteredTreks.length }}</strong> treks
                    </div>
                </div>
            </div>
        </div>

        <!-- Responsive Treks Table Card -->
        <div class="card border-0 shadow-sm rounded-3 overflow-hidden">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light text-secondary text-uppercase small">
                        <tr>
                            <th style="width: 50px;">ID</th>
                            <th>Trek Name & Details</th>
                            <th>Difficulty</th>
                            <th>Dates & Duration</th>
                            <th>Capacity & Slots</th>
                            <th>Assigned Staff</th>
                            <th>Status</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="loading">
                            <td colspan="8" class="text-center py-5 text-muted">
                                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                                Loading trek records...
                            </td>
                        </tr>
                        <tr v-else-if="filteredTreks.length === 0">
                            <td colspan="8" class="text-center py-5 text-muted">
                                <i class="bi bi-map fs-2 d-block mb-2"></i>
                                No matching treks found.
                            </td>
                        </tr>
                        <tr v-for="trek in filteredTreks" :key="trek.id">
                            <td class="fw-bold text-muted">#{{ trek.id }}</td>
                            <td>
                                <div class="fw-bold text-dark">{{ trek.name }}</div>
                                <small class="text-muted"><i class="bi bi-geo-alt me-1"></i>{{ trek.location }}</small>
                            </td>
                            <td>
                                <span class="badge" :class="'badge-diff-' + trek.difficulty">
                                    {{ trek.difficulty }}
                                </span>
                            </td>
                            <td>
                                <div class="small fw-semibold text-dark">{{ trek.duration_days }} Days</div>
                                <small class="text-muted">{{ trek.start_date }} to {{ trek.end_date }}</small>
                            </td>
                            <td>
                                <div class="small">
                                    <strong class="text-success">{{ trek.available_slots }}</strong>
                                    <span class="text-muted"> / {{ trek.total_slots }} available</span>
                                </div>
                                <div class="progress mt-1" style="height: 4px;">
                                    <div class="progress-bar bg-success" 
                                         :style="{ width: ((trek.available_slots / (trek.total_slots || 1)) * 100) + '%' }">
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span v-if="trek.assigned_staff" class="badge bg-light text-dark border">
                                    <i class="bi bi-person-fill text-primary me-1"></i>
                                    {{ trek.assigned_staff.name }}
                                </span>
                                <span v-else class="badge bg-warning bg-opacity-25 text-dark">
                                    Unassigned
                                </span>
                            </td>
                            <td>
                                <!-- Quick Status Selector -->
                                <select 
                                    class="form-select form-select-sm fw-semibold"
                                    :class="'badge-status-' + trek.status"
                                    style="width: 125px;"
                                    :value="trek.status"
                                    @change="updateTrekStatus(trek, $event.target.value)"
                                >
                                    <option value="Pending">Pending</option>
                                    <option value="Approved">Approved</option>
                                    <option value="Open">Open</option>
                                    <option value="Closed">Closed</option>
                                    <option value="Completed">Completed</option>
                                </select>
                            </td>
                            <td class="text-end">
                                <div class="btn-group btn-group-sm">
                                    <button @click="openAssignModal(trek)" 
                                            class="btn btn-outline-secondary" 
                                            title="Assign Staff Guide">
                                        <i class="bi bi-person-plus"></i>
                                    </button>
                                    <button @click="openEditModal(trek)" 
                                            class="btn btn-outline-primary" 
                                            title="Edit Trek">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button @click="openDeleteModal(trek)" 
                                            class="btn btn-outline-danger" 
                                            title="Delete Trek">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Create / Edit Trek Modal -->
        <div v-if="showTrekModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-dark text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-compass text-warning me-2"></i>
                            {{ isEditing ? 'Edit Trek #' + currentTrekId : 'Create New Trek' }}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="showTrekModal = false"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Inline Validation / Error Message -->
                        <div v-if="modalError" class="alert alert-danger d-flex align-items-center gap-2 py-2 small mb-3 shadow-sm" role="alert">
                            <i class="bi bi-exclamation-triangle-fill fs-5 flex-shrink-0"></i>
                            <div><strong>Error:</strong> {{ modalError }}</div>
                        </div>

                        <!-- Inline Success Message -->
                        <div v-if="modalSuccess" class="alert alert-success d-flex align-items-center gap-2 py-2 small mb-3 shadow-sm" role="alert">
                            <i class="bi bi-check-circle-fill fs-5 flex-shrink-0"></i>
                            <div><strong>Success:</strong> {{ modalSuccess }}</div>
                        </div>

                        <form id="trekFormModal" @submit.prevent="saveTrek" novalidate>
                            <div class="row g-3">
                                <div class="col-12 col-md-8">
                                    <label class="form-label small fw-semibold">Trek Name *</label>
                                    <input type="text" 
                                           v-model="trekForm.name" 
                                           class="form-control" 
                                           :class="{'is-invalid': fieldErrors.name}"
                                           placeholder="e.g. Roopkund Mystery Lake Trek" 
                                           required />
                                    <div v-if="fieldErrors.name" class="invalid-feedback d-block">{{ fieldErrors.name }}</div>
                                </div>
                                <div class="col-12 col-md-4">
                                    <label class="form-label small fw-semibold">Difficulty *</label>
                                    <select v-model="trekForm.difficulty" class="form-select" required>
                                        <option value="Easy">Easy</option>
                                        <option value="Moderate">Moderate</option>
                                        <option value="Hard">Hard</option>
                                    </select>
                                </div>

                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold">Location / Region *</label>
                                    <input type="text" 
                                           v-model="trekForm.location" 
                                           class="form-control" 
                                           :class="{'is-invalid': fieldErrors.location}"
                                           placeholder="e.g. Uttarakhand, Himalayas" 
                                           required />
                                    <div v-if="fieldErrors.location" class="invalid-feedback d-block">{{ fieldErrors.location }}</div>
                                </div>

                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold">Operational Status *</label>
                                    <select v-model="trekForm.status" class="form-select" required>
                                        <option value="Open">Open (Accepting Bookings)</option>
                                        <option value="Approved">Approved (Ready)</option>
                                        <option value="Pending">Pending (Draft / Review)</option>
                                        <option value="Closed">Closed</option>
                                        <option value="Completed">Completed</option>
                                    </select>
                                </div>

                                <div class="col-6 col-md-3">
                                    <label class="form-label small fw-semibold">Duration (Days) *</label>
                                    <input type="number" 
                                           v-model="trekForm.duration_days" 
                                           class="form-control" 
                                           :class="{'is-invalid': fieldErrors.duration_days}"
                                           min="1" 
                                           required />
                                    <div v-if="fieldErrors.duration_days" class="invalid-feedback d-block">{{ fieldErrors.duration_days }}</div>
                                </div>
                                <div class="col-6 col-md-3">
                                    <label class="form-label small fw-semibold">Total Capacity Slots *</label>
                                    <input type="number" 
                                           v-model="trekForm.total_slots" 
                                           class="form-control" 
                                           :class="{'is-invalid': fieldErrors.total_slots}"
                                           min="0" 
                                           required />
                                    <div v-if="fieldErrors.total_slots" class="invalid-feedback d-block">{{ fieldErrors.total_slots }}</div>
                                </div>

                                <div class="col-12 col-md-3">
                                    <label class="form-label small fw-semibold">Start Date *</label>
                                    <input type="date" 
                                           v-model="trekForm.start_date" 
                                           class="form-control" 
                                           :class="{'is-invalid': dateErrors.start_date}" 
                                           @change="validateDates"
                                           @input="dateErrors.start_date = ''"
                                           required />
                                    <div v-if="dateErrors.start_date" class="invalid-feedback d-block">
                                        <i class="bi bi-exclamation-circle me-1"></i>{{ dateErrors.start_date }}
                                    </div>
                                </div>
                                <div class="col-12 col-md-3">
                                    <label class="form-label small fw-semibold">End Date *</label>
                                    <input type="date" 
                                           v-model="trekForm.end_date" 
                                           class="form-control" 
                                           :class="{'is-invalid': dateErrors.end_date}" 
                                           @change="validateDates"
                                           @input="dateErrors.end_date = ''"
                                           required />
                                    <div v-if="dateErrors.end_date" class="invalid-feedback d-block">
                                        <i class="bi bi-exclamation-circle me-1"></i>{{ dateErrors.end_date }}
                                    </div>
                                </div>

                                <div class="col-12 col-md-4">
                                    <label class="form-label small fw-semibold">Price per Trekker (₹) *</label>
                                    <input type="number" 
                                           step="0.01" 
                                           v-model="trekForm.price" 
                                           class="form-control" 
                                           :class="{'is-invalid': fieldErrors.price}"
                                           min="0" 
                                           required />
                                    <div v-if="fieldErrors.price" class="invalid-feedback d-block">{{ fieldErrors.price }}</div>
                                </div>

                                <div class="col-12">
                                    <label class="form-label small fw-semibold">Trek Description *</label>
                                    <textarea v-model="trekForm.description" 
                                              class="form-control" 
                                              :class="{'is-invalid': fieldErrors.description}"
                                              rows="3" 
                                              placeholder="Provide overview, scenic highlights, and trail summary (minimum 10 characters)..." 
                                              required></textarea>
                                    <div v-if="fieldErrors.description" class="invalid-feedback d-block">{{ fieldErrors.description }}</div>
                                </div>

                                <div class="col-12">
                                    <label class="form-label small fw-semibold">Packing & Trail Instructions</label>
                                    <textarea v-model="trekForm.instructions" 
                                              class="form-control" 
                                              rows="2" 
                                              placeholder="Gear needed, weather cautions, physical prep tips..."></textarea>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary" @click="showTrekModal = false">Cancel</button>
                        <button type="submit" form="trekFormModal" class="btn btn-primary" :disabled="actionLoading" @click="saveTrek">
                            <span v-if="actionLoading" class="spinner-border spinner-border-sm me-1"></span>
                            {{ isEditing ? 'Save Changes' : 'Create Trek' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Assign Staff Modal -->
        <div v-if="showAssignModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-dark text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-person-badge-fill text-warning me-2"></i>Assign Staff Guide
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="showAssignModal = false"></button>
                    </div>
                    <div class="modal-body">
                        <p class="small text-muted mb-3">
                            Assign an active staff coordinator or mountain guide to lead:
                            <br><strong class="text-dark">{{ assignTrek ? assignTrek.name : '' }}</strong>
                        </p>
                        <div class="mb-3">
                            <label class="form-label small fw-semibold">Select Active Staff</label>
                            <select v-model="selectedStaffId" class="form-select">
                                <option value="">-- Choose Staff Member --</option>
                                <option v-for="s in staffList" :key="s.id" :value="s.id">
                                    {{ s.name }} ({{ s.specialization || 'Guide' }}) - {{ s.email }}
                                </option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" @click="showAssignModal = false">Cancel</button>
                        <button type="button" class="btn btn-primary btn-sm" :disabled="actionLoading" @click="submitAssignment">
                            <span v-if="actionLoading" class="spinner-border spinner-border-sm me-1"></span>
                            Assign Staff
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Trek Confirmation Modal -->
        <div v-if="showDeleteModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>Confirm Delete Trek
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="showDeleteModal = false"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to soft-delete <strong>{{ deleteTrekTarget ? deleteTrekTarget.name : '' }}</strong>?</p>
                        <div class="form-check mt-3 p-3 bg-light rounded border">
                            <input class="form-check-input" type="checkbox" id="cancelBookingsCheck" v-model="cancelActiveBookings">
                            <label class="form-check-label small" for="cancelBookingsCheck">
                                <strong>Cancel existing active bookings</strong> automatically and notify enrolled participants.
                            </label>
                        </div>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" @click="showDeleteModal = false">Abort</button>
                        <button type="button" class="btn btn-danger btn-sm" :disabled="actionLoading" @click="confirmDelete">
                            <span v-if="actionLoading" class="spinner-border spinner-border-sm me-1"></span>
                            Confirm Delete
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.AdminTreks = AdminTreks;

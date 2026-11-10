/**
 * StaffTrekDetail Component
 * In-depth expedition management:
 * - Edit available and total slots with client-side integer >= 0 validation
 * - Open/Closed toggle
 * - "Start Trek" and "Mark Completed" with confirmation dialogs
 * - Participant table (name, phone, emergency contact, booking status)
 * - Friendly messages for 403 and 409 errors
 */

const StaffTrekDetail = {
    name: 'StaffTrekDetail',
    data() {
        return {
            trekId: null,
            trek: null,
            participants: [],
            loading: true,
            actionLoading: false,

            // Error & Friendly message states
            errorMessage: '',
            errorCode: null,

            // Slot Edit Form
            slotForm: {
                total_slots: 0,
                available_slots: 0
            },
            slotErrors: '',

            // Confirmation Modal states
            showStartModal: false,
            showCompleteModal: false
        };
    },
    computed: {
        bookedSlotsCount() {
            if (!this.trek) return 0;
            return (this.trek.total_slots || 0) - (this.trek.available_slots || 0);
        }
    },
    methods: {
        async loadTrekDetail() {
            this.loading = true;
            this.errorMessage = '';
            this.errorCode = null;
            this.trekId = this.$route.params.id;

            try {
                // 1. Fetch assigned treks to locate current trek
                const treksRes = await window.tmaApi.get('/staff/treks');
                if (treksRes && treksRes.data) {
                    const found = treksRes.data.find(t => String(t.id) === String(this.trekId));
                    if (!found) {
                        this.errorCode = 403;
                        this.errorMessage = "Access Restricted: You are not authorized to manage this trek. Staff members can only view and operate treks specifically assigned to them.";
                        this.loading = false;
                        return;
                    }
                    this.trek = found;
                    this.slotForm = {
                        total_slots: found.total_slots,
                        available_slots: found.available_slots
                    };
                }

                // 2. Fetch participant roster
                const partsRes = await window.tmaApi.get(`/staff/treks/${this.trekId}/participants`);
                if (partsRes && partsRes.data) {
                    this.participants = partsRes.data.participants || [];
                }
            } catch (err) {
                this.handleApiError(err, "Failed to load trek details.");
            } finally {
                this.loading = false;
            }
        },

        handleApiError(err, fallbackMsg) {
            this.errorCode = err.status || null;
            if (err.status === 403) {
                this.errorMessage = "Access Forbidden: You are not authorized to access or modify this trek. Staff members may only manage expeditions assigned directly to them.";
            } else if (err.status === 409) {
                this.errorMessage = `Conflict Error: ${err.message || 'Cannot perform operation due to conflicting bookings or slot restrictions.'}`;
            } else if (err.status === 400) {
                this.errorMessage = `Invalid Request: ${err.message || 'Please check your inputs and try again.'}`;
            } else {
                this.errorMessage = err.message || fallbackMsg;
            }
            window.showToast(this.errorMessage, "danger");
        },

        async saveSlots() {
            this.slotErrors = '';
            const total = parseInt(this.slotForm.total_slots, 10);
            const avail = parseInt(this.slotForm.available_slots, 10);

            // Validation: integer >= 0
            if (isNaN(avail) || avail < 0) {
                this.slotErrors = "Available slots must be a non-negative integer (>= 0).";
                return;
            }
            if (isNaN(total) || total < 0) {
                this.slotErrors = "Total slots must be a valid positive integer.";
                return;
            }
            if (avail > total) {
                this.slotErrors = "Available slots cannot exceed total capacity slots.";
                return;
            }
            if (total < this.bookedSlotsCount) {
                this.slotErrors = `Total capacity cannot be set below currently booked participant count (${this.bookedSlotsCount}).`;
                return;
            }

            this.actionLoading = true;
            try {
                const res = await window.tmaApi.put(`/staff/treks/${this.trekId}/slots`, {
                    total_slots: total,
                    available_slots: avail
                });
                if (res && res.data) {
                    this.trek.total_slots = res.data.total_slots;
                    this.trek.available_slots = res.data.available_slots;
                }
                window.showToast("Slots updated successfully!", "success");
            } catch (err) {
                this.handleApiError(err, "Failed to update slots.");
            } finally {
                this.actionLoading = false;
            }
        },

        async toggleStatus() {
            if (!this.trek) return;
            const targetStatus = this.trek.status === 'Open' ? 'Closed' : 'Open';
            this.actionLoading = true;
            try {
                const res = await window.tmaApi.put(`/staff/treks/${this.trekId}/status`, {
                    status: targetStatus
                });
                if (res && res.data) {
                    this.trek.status = res.data.status;
                } else {
                    this.trek.status = targetStatus;
                }
                window.showToast(`Trek status toggled to '${this.trek.status}'.`, "success");
            } catch (err) {
                this.handleApiError(err, "Failed to toggle trek status.");
            } finally {
                this.actionLoading = false;
            }
        },

        async executeStartTrek() {
            this.actionLoading = true;
            try {
                await window.tmaApi.post(`/staff/treks/${this.trekId}/start`);
                this.trek.is_started = true;
                window.showToast("Trek marked as Started! Expedition is now underway.", "success");
                this.showStartModal = false;
            } catch (err) {
                this.handleApiError(err, "Could not start trek.");
            } finally {
                this.actionLoading = false;
            }
        },

        async executeCompleteTrek() {
            this.actionLoading = true;
            try {
                await window.tmaApi.post(`/staff/treks/${this.trekId}/complete`);
                this.trek.status = 'Completed';
                // Transition active participant bookings to Completed in local state
                this.participants.forEach(p => {
                    if (p.booking_status === 'Booked') p.booking_status = 'Completed';
                });
                window.showToast("Trek completed successfully! All bookings transitioned to Completed.", "success");
                this.showCompleteModal = false;
            } catch (err) {
                this.handleApiError(err, "Could not complete trek.");
            } finally {
                this.actionLoading = false;
            }
        }
    },
    mounted() {
        this.loadTrekDetail();
    },
    template: `
    <div class="container py-4">
        <!-- Back Navigation Breadcrumb -->
        <div class="mb-3">
            <router-link to="/staff" class="btn btn-outline-secondary btn-sm d-inline-flex align-items-center gap-1">
                <i class="bi bi-arrow-left"></i> Back to Staff Dashboard
            </router-link>
        </div>

        <!-- 403 Forbidden Friendly Alert -->
        <div v-if="errorCode === 403" class="card border-danger border-2 shadow-sm rounded-3 p-4 text-center my-4">
            <div class="text-danger mb-3">
                <i class="bi bi-shield-slash-fill display-3"></i>
            </div>
            <h4 class="fw-bold text-danger">Access Restricted (403 Forbidden)</h4>
            <p class="text-muted mb-4 max-w-md mx-auto">
                {{ errorMessage }}
            </p>
            <div>
                <router-link to="/staff" class="btn btn-primary btn-sm">
                    <i class="bi bi-house-door me-1"></i> Return to My Assigned Treks
                </router-link>
            </div>
        </div>

        <!-- Loading State -->
        <div v-else-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <div class="mt-2 text-muted small">Loading expedition details & participant manifest...</div>
        </div>

        <!-- Main Trek Detail Body -->
        <div v-else-if="trek">
            <!-- Header Card -->
            <div class="card border-0 shadow-sm rounded-3 mb-4 overflow-hidden">
                <div class="card-body p-4">
                    <div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-3">
                        <div>
                            <div class="d-flex align-items-center gap-2 mb-2">
                                <span class="badge" :class="'badge-diff-' + trek.difficulty">{{ trek.difficulty }}</span>
                                <span class="badge" :class="'badge-status-' + trek.status">{{ trek.status }}</span>
                                <span v-if="trek.is_started && trek.status !== 'Completed'" class="badge bg-warning text-dark">
                                    <i class="bi bi-play-circle-fill me-1"></i>Expedition Started
                                </span>
                            </div>
                            <h2 class="fw-bold text-dark mb-1">{{ trek.name }}</h2>
                            <p class="text-muted small mb-2">
                                <i class="bi bi-geo-alt-fill text-danger me-1"></i>{{ trek.location }}
                            </p>
                            <p class="text-secondary small mb-0">{{ trek.description }}</p>
                        </div>

                        <!-- Schedule Badge Box -->
                        <div class="p-3 bg-light rounded text-md-end text-start border flex-shrink-0" style="min-width: 220px;">
                            <div class="small text-muted mb-1">
                                <i class="bi bi-calendar3 me-1"></i><strong>{{ trek.start_date }}</strong> to <strong>{{ trek.end_date }}</strong>
                            </div>
                            <div class="small text-muted mb-1">
                                <i class="bi bi-clock me-1"></i>Duration: <strong>{{ trek.duration_days }} Days</strong>
                            </div>
                            <div class="small text-muted">
                                <i class="bi bi-tag me-1"></i>Price: <strong>₹{{ trek.price ? trek.price.toLocaleString() : 0 }}</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Controls Grid: Slot Editor & Expedition Actions -->
            <div class="row g-4 mb-4">
                <!-- 1. Slot Capacities Editor Card -->
                <div class="col-12 col-lg-6">
                    <div class="card border-0 shadow-sm rounded-3 h-100">
                        <div class="card-header bg-white py-3 border-0">
                            <h5 class="fw-bold text-dark mb-0">
                                <i class="bi bi-sliders text-primary me-2"></i>Edit Available & Total Slots
                            </h5>
                        </div>
                        <div class="card-body pt-0">
                            <p class="text-muted small">
                                Adjust the available slots open for booking. Form validation enforces that available slots must be an integer &ge; 0.
                            </p>

                            <div v-if="slotErrors" class="alert alert-warning small py-2 d-flex align-items-center gap-2">
                                <i class="bi bi-exclamation-triangle-fill"></i>
                                <div>{{ slotErrors }}</div>
                            </div>

                            <form @submit.prevent="saveSlots">
                                <div class="row g-3 mb-3">
                                    <div class="col-6">
                                        <label class="form-label small fw-semibold text-secondary">Total Capacity Slots</label>
                                        <input 
                                            type="number" 
                                            v-model="slotForm.total_slots" 
                                            class="form-control" 
                                            min="0" 
                                            step="1"
                                            :disabled="trek.status === 'Completed'"
                                            required 
                                        />
                                        <div class="form-text small" style="font-size: 0.75rem;">Total slots for trek</div>
                                    </div>
                                    <div class="col-6">
                                        <label class="form-label small fw-semibold text-secondary">Available Slots *</label>
                                        <input 
                                            type="number" 
                                            v-model="slotForm.available_slots" 
                                            class="form-control" 
                                            min="0" 
                                            step="1"
                                            :disabled="trek.status === 'Completed'"
                                            required 
                                        />
                                        <div class="form-text small" style="font-size: 0.75rem;">Must be integer &ge; 0</div>
                                    </div>
                                </div>

                                <div class="p-2 bg-light rounded small mb-3 d-flex justify-content-between">
                                    <span class="text-muted">Current Active Bookings:</span>
                                    <strong class="text-primary">{{ bookedSlotsCount }} slots</strong>
                                </div>

                                <button 
                                    type="submit" 
                                    class="btn btn-primary btn-sm px-4 fw-semibold"
                                    :disabled="actionLoading || trek.status === 'Completed'"
                                >
                                    <span v-if="actionLoading" class="spinner-border spinner-border-sm me-1"></span>
                                    Save Slot Changes
                                </button>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- 2. Expedition Operations & Status Card -->
                <div class="col-12 col-lg-6">
                    <div class="card border-0 shadow-sm rounded-3 h-100">
                        <div class="card-header bg-white py-3 border-0">
                            <h5 class="fw-bold text-dark mb-0">
                                <i class="bi bi-toggles text-warning me-2"></i>Expedition Status & Trail Controls
                            </h5>
                        </div>
                        <div class="card-body pt-0 d-flex flex-column justify-content-between">
                            <div>
                                <p class="text-muted small">
                                    Control registration intake by toggling between Open and Closed, initiate trek tracking, or conclude expedition upon return.
                                </p>

                                <div class="d-flex flex-wrap gap-2 mb-3">
                                    <!-- Open/Closed Toggle Button -->
                                    <button 
                                        v-if="['Approved', 'Open', 'Closed'].includes(trek.status)"
                                        @click="toggleStatus" 
                                        class="btn btn-sm d-flex align-items-center gap-2 fw-semibold"
                                        :class="trek.status === 'Open' ? 'btn-outline-warning' : 'btn-outline-success'"
                                        :disabled="actionLoading"
                                    >
                                        <i class="bi" :class="trek.status === 'Open' ? 'bi-lock-fill' : 'bi-unlock-fill'"></i>
                                        <span>{{ trek.status === 'Open' ? 'Close Trek Registration' : 'Open Trek Registration' }}</span>
                                    </button>

                                    <!-- Start Trek Button (with Confirm Dialog) -->
                                    <button 
                                        v-if="!trek.is_started && trek.status !== 'Completed'"
                                        @click="showStartModal = true" 
                                        class="btn btn-info btn-sm text-dark d-flex align-items-center gap-2 fw-semibold"
                                        :disabled="actionLoading"
                                    >
                                        <i class="bi bi-play-fill fs-6"></i>
                                        <span>Start Trek</span>
                                    </button>

                                    <!-- Mark Completed Button (with Confirm Dialog) -->
                                    <button 
                                        v-if="trek.status !== 'Completed'"
                                        @click="showCompleteModal = true" 
                                        class="btn btn-success btn-sm d-flex align-items-center gap-2 fw-semibold"
                                        :disabled="actionLoading"
                                    >
                                        <i class="bi bi-check2-circle fs-6"></i>
                                        <span>Mark Completed</span>
                                    </button>
                                </div>
                            </div>

                            <div v-if="trek.status === 'Completed'" class="alert alert-success small mb-0">
                                <i class="bi bi-check-circle-fill me-1"></i>
                                This trek has been marked as <strong>Completed</strong>. All participants have concluded the journey.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Participant Table Card -->
            <div class="card border-0 shadow-sm rounded-3 overflow-hidden">
                <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
                    <h5 class="fw-bold text-dark mb-0">
                        <i class="bi bi-people-fill text-primary me-2"></i>Registered Participant Manifest ({{ participants.length }})
                    </h5>
                    <span class="badge bg-light text-dark border">
                        Total Enrolled: {{ participants.reduce((acc, p) => acc + (p.participants_count || 1), 0) }}
                    </span>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light text-secondary text-uppercase small">
                            <tr>
                                <th>Participant Name</th>
                                <th>Contact Phone</th>
                                <th>Emergency Contact</th>
                                <th>Registered Slots</th>
                                <th class="text-end">Booking Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-if="participants.length === 0">
                                <td colspan="5" class="text-center py-5 text-muted">
                                    <i class="bi bi-person-x fs-2 d-block mb-2"></i>
                                    No participants enrolled in this expedition yet.
                                </td>
                            </tr>
                            <tr v-for="(p, idx) in participants" :key="idx">
                                <td>
                                    <div class="fw-bold text-dark">{{ p.name }}</div>
                                    <small class="text-muted">{{ p.email }}</small>
                                </td>
                                <td class="small">{{ p.phone || 'N/A' }}</td>
                                <td class="small text-muted">{{ p.emergency_contact || 'None specified' }}</td>
                                <td>
                                    <span class="badge bg-light text-dark border">
                                        {{ p.participants_count || 1 }} trekker(s)
                                    </span>
                                </td>
                                <td class="text-end">
                                    <span class="badge" 
                                          :class="{
                                              'bg-primary': p.booking_status === 'Booked',
                                              'bg-success': p.booking_status === 'Completed',
                                              'bg-danger': p.booking_status === 'Cancelled'
                                          }">
                                        {{ p.booking_status }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Confirm Dialog Modal: Start Trek -->
        <div v-if="showStartModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-info text-dark">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-play-fill me-1"></i>Confirm: Start Expedition
                        </h5>
                        <button type="button" class="btn-close" @click="showStartModal = false"></button>
                    </div>
                    <div class="modal-body p-4">
                        <p>Are you ready to mark <strong>{{ trek ? trek.name : '' }}</strong> as officially started?</p>
                        <p class="small text-muted mb-0">
                            This records that participants and guide are on the trail and the expedition is actively in progress.
                        </p>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" @click="showStartModal = false">Cancel</button>
                        <button type="button" class="btn btn-info btn-sm text-dark fw-bold" :disabled="actionLoading" @click="executeStartTrek">
                            <span v-if="actionLoading" class="spinner-border spinner-border-sm me-1"></span>
                            Yes, Start Trek
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Confirm Dialog Modal: Mark Completed -->
        <div v-if="showCompleteModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-check2-circle me-1"></i>Confirm: Mark Completed
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="showCompleteModal = false"></button>
                    </div>
                    <div class="modal-body p-4">
                        <p>Are you sure you want to finalize and mark <strong>{{ trek ? trek.name : '' }}</strong> as completed?</p>
                        <div class="alert alert-warning small mb-0">
                            <i class="bi bi-exclamation-triangle-fill me-1"></i>
                            This will transition the trek status to <strong>Completed</strong> and automatically update all active enrolled participant bookings to <strong>Completed</strong>.
                        </div>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" @click="showCompleteModal = false">Cancel</button>
                        <button type="button" class="btn btn-success btn-sm fw-bold" :disabled="actionLoading" @click="executeCompleteTrek">
                            <span v-if="actionLoading" class="spinner-border spinner-border-sm me-1"></span>
                            Yes, Mark Completed
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.StaffTrekDetail = StaffTrekDetail;


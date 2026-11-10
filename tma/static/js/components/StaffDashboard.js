/**
 * StaffDashboard Component
 * Displays summary cards for each trek assigned to the logged-in staff member,
 * including registered-user count, status badges, dates, and slots.
 */

const StaffDashboard = {
    name: 'StaffDashboard',
    data() {
        return {
            loading: true,
            treks: [],
            totalTreksCount: 0,
            totalRegisteredUsers: 0,
            errorMessage: ''
        };
    },
    methods: {
        async fetchStaffTreks() {
            this.loading = true;
            this.errorMessage = '';
            try {
                // GET /api/staff/dashboard returns assigned treks and registered count
                const res = await window.tmaApi.get('/staff/dashboard');
                if (res && res.data) {
                    this.treks = res.data.treks || [];
                    this.totalTreksCount = (res.data.summary && res.data.summary.total_assigned_treks) !== undefined 
                        ? res.data.summary.total_assigned_treks 
                        : this.treks.length;
                    this.totalRegisteredUsers = (res.data.summary && res.data.summary.total_participants) !== undefined
                        ? res.data.summary.total_participants
                        : (res.data.summary && res.data.summary.total_booked_users) || 0;
                }
            } catch (err) {
                if (err.status === 403) {
                    this.errorMessage = "Access Restricted: You do not have permission to view staff portal records.";
                } else {
                    this.errorMessage = err.message || "Failed to load assigned treks.";
                }
                window.showToast(this.errorMessage, "danger");
            } finally {
                this.loading = false;
            }
        },

        goToTrekDetail(trekId) {
            this.$router.push(`/staff/treks/${trekId}`);
        }
    },
    mounted() {
        this.fetchStaffTreks();
    },
    template: `
    <div class="container py-4">
        <!-- Title Banner -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-person-workspace text-warning me-2"></i>Staff Operations Dashboard
                </h3>
                <p class="text-muted small mb-0">Overview of your assigned mountain expeditions and registered participant groups.</p>
            </div>
            <button @click="fetchStaffTreks" class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1 shadow-sm">
                <i class="bi bi-arrow-clockwise"></i> Refresh Treks
            </button>
        </div>

        <!-- Friendly Error Alert -->
        <div v-if="errorMessage" class="alert alert-danger d-flex align-items-center gap-2 mb-4" role="alert">
            <i class="bi bi-exclamation-octagon-fill fs-5"></i>
            <div>{{ errorMessage }}</div>
        </div>

        <!-- Metric KPI Cards -->
        <div class="row g-3 mb-4">
            <div class="col-12 col-sm-6">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-warning h-100">
                    <div class="card-body d-flex justify-content-between align-items-center">
                        <div>
                            <span class="text-muted small fw-semibold text-uppercase">Assigned Expeditions</span>
                            <h2 class="fw-bold text-dark mt-1 mb-0">{{ totalTreksCount }}</h2>
                        </div>
                        <div class="p-3 bg-warning bg-opacity-10 text-warning rounded-circle">
                            <i class="bi bi-compass-fill fs-3 text-dark"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-12 col-sm-6">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-primary h-100">
                    <div class="card-body d-flex justify-content-between align-items-center">
                        <div>
                            <span class="text-muted small fw-semibold text-uppercase">Enrolled Trekkers</span>
                            <h2 class="fw-bold text-dark mt-1 mb-0">{{ totalRegisteredUsers }}</h2>
                        </div>
                        <div class="p-3 bg-primary bg-opacity-10 text-primary rounded-circle">
                            <i class="bi bi-people-fill fs-3"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <div class="mt-2 text-muted small">Loading your assigned expeditions...</div>
        </div>

        <!-- Empty State -->
        <div v-else-if="treks.length === 0" class="card border-0 shadow-sm p-5 text-center text-muted rounded-3">
            <i class="bi bi-binoculars display-4 text-secondary mb-3 d-block"></i>
            <h4>No Expeditions Assigned</h4>
            <p class="small text-muted mb-0">You currently have no mountain treks assigned under your staff profile. Contact an administrator to assign treks.</p>
        </div>

        <!-- Assigned Trek Cards Grid -->
        <div v-else class="row g-4">
            <div v-for="t in treks" :key="t.id" class="col-12 col-md-6 col-lg-4">
                <div class="card border-0 shadow-sm rounded-3 h-100 hover-shadow d-flex flex-column">
                    <div class="card-body p-4 d-flex flex-column">
                        <!-- Top Badges -->
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="badge" :class="'badge-diff-' + t.difficulty">
                                {{ t.difficulty }}
                            </span>
                            <span class="badge" :class="'badge-status-' + t.status">
                                {{ t.status }}
                            </span>
                        </div>

                        <!-- Trek Title -->
                        <h5 class="fw-bold text-dark mb-1">{{ t.name }}</h5>
                        <p class="text-muted small mb-3">
                            <i class="bi bi-geo-alt-fill text-danger me-1"></i>{{ t.location }}
                        </p>

                        <!-- Started / Progress Flag -->
                        <div v-if="t.is_started && t.status !== 'Completed'" class="mb-3">
                            <span class="badge bg-warning text-dark">
                                <i class="bi bi-play-circle-fill me-1"></i>Expedition In Progress
                            </span>
                        </div>

                        <!-- Trek Details Grid -->
                        <div class="p-3 bg-light rounded small mb-3 flex-grow-1">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted"><i class="bi bi-calendar3 me-1"></i>Dates:</span>
                                <strong class="text-dark">{{ t.start_date }} to {{ t.end_date }}</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted"><i class="bi bi-clock me-1"></i>Duration:</span>
                                <strong class="text-dark">{{ t.duration_days }} Days</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted"><i class="bi bi-people me-1"></i>Registered Users:</span>
                                <strong class="text-primary">{{ t.registered_users_count || 0 }} Trekkers</strong>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span class="text-muted"><i class="bi bi-pie-chart me-1"></i>Slots Available:</span>
                                <strong :class="t.available_slots > 0 ? 'text-success' : 'text-danger'">
                                    {{ t.available_slots }} / {{ t.total_slots }}
                                </strong>
                            </div>
                        </div>

                        <!-- Card Action -->
                        <div class="pt-3 border-top mt-auto d-flex justify-content-between align-items-center">
                            <span class="text-muted small">Trek ID: #{{ t.id }}</span>
                            <button 
                                @click="goToTrekDetail(t.id)" 
                                class="btn btn-primary btn-sm px-3 fw-semibold shadow-sm d-flex align-items-center gap-1"
                            >
                                <span>Manage Trek</span>
                                <i class="bi bi-arrow-right"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.StaffDashboard = StaffDashboard;

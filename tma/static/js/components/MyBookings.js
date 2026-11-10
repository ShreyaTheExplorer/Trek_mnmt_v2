
/**
 * MyBookings Component
 * Trekker reservations portal:
 * - Active bookings management (payment simulation, cancellation with slot restoration)
 * - Booking history (Completed and Cancelled)
 * - Asynchronous Celery CSV export trigger, polling, and secure download
 */

const MyBookings = {
    name: 'MyBookings',
    data() {
        return {
            loading: true,
            dashboardStats: {
                available_treks_count: 0,
                status_counts: { Booked: 0, Completed: 0, Cancelled: 0 },
                total_bookings: 0
            },
            activeBookings: [],
            historyBookings: [],
            activeTab: 'active', // 'active' | 'history'

            // Cancellation Modal State
            showCancelModal: false,
            cancelTargetBooking: null,
            cancelLoading: false,

            // CSV Export State
            exportLoading: false,
            exportTaskId: null,
            exportStatus: '',
            exportReady: false,
            exportDownloadUrl: null,
            exportFilename: null,
            exportPollTimer: null
        };
    },
    methods: {
        async fetchUserBookingsData() {
            this.loading = true;
            try {
                const [dashRes, bookRes, histRes] = await Promise.all([
                    window.tmaApi.get('/user/dashboard'),
                    window.tmaApi.get('/user/bookings'),
                    window.tmaApi.get('/user/history')
                ]);

                if (dashRes && dashRes.data) {
                    this.dashboardStats = dashRes.data;
                }
                if (bookRes && bookRes.data) {
                    this.activeBookings = bookRes.data;
                }
                if (histRes && histRes.data) {
                    this.historyBookings = histRes.data;
                }
            } catch (err) {
                window.showToast("Failed to load your bookings: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        async simulatePayment(booking) {
            try {
                await window.tmaApi.post(`/user/bookings/${booking.id}/pay`);
                booking.payment_status = 'Paid';
                window.showToast(`Payment of ₹${((booking.participants_count || 1) * (booking.trek ? booking.trek.price : 0)).toLocaleString()} simulated successfully!`, "success");
            } catch (err) {
                window.showToast("Payment simulation failed: " + err.message, "danger");
            }
        },

        openCancelModal(booking) {
            this.cancelTargetBooking = booking;
            this.showCancelModal = true;
        },

        async confirmCancelBooking() {
            if (!this.cancelTargetBooking) return;
            this.cancelLoading = true;
            try {
                await window.tmaApi.post(`/user/bookings/${this.cancelTargetBooking.id}/cancel`);
                window.showToast("Booking cancelled successfully. Reserved slots have been restored.", "success");
                this.showCancelModal = false;
                await this.fetchUserBookingsData();
            } catch (err) {
                window.showToast("Cancellation failed: " + err.message, "danger");
            } finally {
                this.cancelLoading = false;
            }
        },

        async triggerCsvExport() {
            this.exportLoading = true;
            this.exportReady = false;
            this.exportStatus = 'Initiating export job...';
            this.exportDownloadUrl = null;
            this.exportFilename = null;

            try {
                const res = await window.tmaApi.post('/user/export');
                if (res && res.data) {
                    const taskId = res.data.task_id || res.data.job_id;
                    this.exportTaskId = taskId;
                    this.exportStatus = 'Processing CSV on background worker...';

                    // Start polling task status
                    this.pollExportTask(taskId);
                }
            } catch (err) {
                this.exportLoading = false;
                window.showToast("Could not initiate CSV export: " + err.message, "danger");
            }
        },

        pollExportTask(taskId) {
            if (this.exportPollTimer) clearInterval(this.exportPollTimer);

            let pollAttempts = 0;
            this.exportPollTimer = setInterval(async () => {
                pollAttempts++;
                try {
                    const res = await window.tmaApi.get(`/user/export/${taskId}`);
                    if (res && res.data) {
                        const { status, ready, download_url, filename } = res.data;
                        this.exportStatus = `Job Status: ${status}`;

                        if (ready || status === 'SUCCESS') {
                            clearInterval(this.exportPollTimer);
                            this.exportLoading = false;
                            this.exportReady = true;
                            this.exportDownloadUrl = download_url;
                            this.exportFilename = filename;
                            window.showToast("Your CSV export is ready for download!", "success");
                        } else if (status === 'FAILURE') {
                            clearInterval(this.exportPollTimer);
                            this.exportLoading = false;
                            window.showToast("CSV Export task failed on background worker.", "danger");
                        }
                    }
                } catch (e) {
                    // Stop polling after 15 attempts (30s)
                    if (pollAttempts > 15) {
                        clearInterval(this.exportPollTimer);
                        this.exportLoading = false;
                        window.showToast("Export polling timed out.", "warning");
                    }
                }
            }, 1500);
        },

        async downloadExportFile() {
            if (!this.exportFilename) return;
            try {
                const blob = await window.tmaApi.get(`/user/exports/${this.exportFilename}`);
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = this.exportFilename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            } catch (err) {
                window.showToast("Download failed: " + err.message, "danger");
            }
        }
    },
    mounted() {
        this.fetchUserBookingsData();
    },
    beforeUnmount() {
        if (this.exportPollTimer) clearInterval(this.exportPollTimer);
    },
    template: `
    <div class="container py-4">
        <!-- Title Banner with Export Action -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-journal-bookmark-fill text-primary me-2"></i>My Bookings & Expeditions
                </h3>
                <p class="text-muted small mb-0">Track active mountain reservations, simulate payment settlements, and review expedition history.</p>
            </div>
            <div class="d-flex flex-wrap gap-2">
                <button @click="fetchUserBookingsData" class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1">
                    <i class="bi bi-arrow-clockwise"></i> Refresh
                </button>
                <button 
                    @click="triggerCsvExport" 
                    class="btn btn-success btn-sm d-flex align-items-center gap-2 fw-semibold shadow-sm"
                    :disabled="exportLoading"
                >
                    <span v-if="exportLoading" class="spinner-border spinner-border-sm"></span>
                    <i v-else class="bi bi-file-earmark-spreadsheet-fill"></i>
                    <span>Export Bookings (CSV)</span>
                </button>
            </div>
        </div>

        <!-- CSV Export Progress & Download Banner -->
        <div v-if="exportLoading || exportReady" class="card border-0 shadow-sm rounded-3 mb-4 border-start border-4 border-success">
            <div class="card-body p-3 d-flex flex-column flex-sm-row justify-content-between align-items-sm-center gap-3">
                <div class="d-flex align-items-center gap-2">
                    <div v-if="exportLoading" class="spinner-border spinner-border-sm text-success"></div>
                    <i v-else class="bi bi-check-circle-fill text-success fs-5"></i>
                    <div>
                        <strong class="text-dark">{{ exportReady ? 'Export File Ready!' : 'Generating Export CSV...' }}</strong>
                        <div class="small text-muted">{{ exportStatus }}</div>
                    </div>
                </div>
                <div v-if="exportReady && exportDownloadUrl">
                    <button @click="downloadExportFile" class="btn btn-primary btn-sm px-3 fw-semibold">
                        <i class="bi bi-download me-1"></i>Download CSV File
                    </button>
                </div>
            </div>
        </div>

        <!-- KPI Metric Cards Grid -->
        <div class="row g-3 mb-4">
            <div class="col-6 col-md-3">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-primary h-100">
                    <div class="card-body p-3">
                        <span class="text-muted small fw-semibold text-uppercase">Active Bookings</span>
                        <h3 class="fw-bold text-dark mt-1 mb-0">{{ dashboardStats.status_counts.Booked || 0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-success h-100">
                    <div class="card-body p-3">
                        <span class="text-muted small fw-semibold text-uppercase">Completed</span>
                        <h3 class="fw-bold text-dark mt-1 mb-0">{{ dashboardStats.status_counts.Completed || 0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-danger h-100">
                    <div class="card-body p-3">
                        <span class="text-muted small fw-semibold text-uppercase">Cancelled</span>
                        <h3 class="fw-bold text-dark mt-1 mb-0">{{ dashboardStats.status_counts.Cancelled || 0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-info h-100">
                    <div class="card-body p-3">
                        <span class="text-muted small fw-semibold text-uppercase">Available Treks</span>
                        <h3 class="fw-bold text-dark mt-1 mb-0">{{ dashboardStats.available_treks_count || 0 }}</h3>
                    </div>
                </div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <ul class="nav nav-tabs mb-4">
            <li class="nav-item">
                <button class="nav-link fw-semibold" :class="{ active: activeTab === 'active' }" @click="activeTab = 'active'">
                    <i class="bi bi-calendar2-check me-1"></i>Active Reservations ({{ activeBookings.length }})
                </button>
            </li>
            <li class="nav-item">
                <button class="nav-link fw-semibold" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">
                    <i class="bi bi-clock-history me-1"></i>Booking History ({{ historyBookings.length }})
                </button>
            </li>
        </ul>

        <!-- Loading Spinner -->
        <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <div class="mt-2 text-muted small">Loading your reservation records...</div>
        </div>

        <!-- TAB 1: Active Bookings -->
        <div v-else-if="activeTab === 'active'">
            <div v-if="activeBookings.length === 0" class="card border-0 shadow-sm p-5 text-center text-muted rounded-3">
                <i class="bi bi-ticket-perforated display-4 text-secondary mb-3 d-block"></i>
                <h5>No Active Reservations</h5>
                <p class="small text-muted mb-3">You do not have any upcoming mountain bookings registered.</p>
                <div>
                    <router-link to="/treks" class="btn btn-primary btn-sm px-3">
                        <i class="bi bi-map me-1"></i>Explore Trekking Catalog
                    </router-link>
                </div>
            </div>

            <div v-else class="row g-4">
                <div v-for="b in activeBookings" :key="b.id" class="col-12 col-md-6 col-lg-4">
                    <div class="card border-0 shadow-sm rounded-3 h-100 d-flex flex-column">
                        <div class="card-body p-4 d-flex flex-column">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <span class="badge bg-primary">Active Reservation</span>
                                <span class="badge" 
                                      :class="b.payment_status === 'Paid' ? 'bg-success' : 'bg-warning text-dark'">
                                    <i class="bi" :class="b.payment_status === 'Paid' ? 'bi-check-circle me-1' : 'bi-hourglass-split me-1'"></i>
                                    {{ b.payment_status }}
                                </span>
                            </div>

                            <h5 class="fw-bold text-dark mb-1">{{ b.trek ? b.trek.name : 'Mountain Trek' }}</h5>
                            <p class="text-muted small mb-3">
                                <i class="bi bi-geo-alt-fill text-danger me-1"></i>{{ b.trek ? b.trek.location : 'Himalayas' }}
                            </p>

                            <!-- Reservation Details -->
                            <div class="p-3 bg-light rounded small mb-3 flex-grow-1">
                                <div class="d-flex justify-content-between mb-1">
                                    <span class="text-muted">Start Date:</span>
                                    <strong class="text-dark">{{ b.trek ? b.trek.start_date : 'N/A' }}</strong>
                                </div>
                                <div class="d-flex justify-content-between mb-1">
                                    <span class="text-muted">Enrolled Trekkers:</span>
                                    <strong class="text-dark">{{ b.participants_count }} Person(s)</strong>
                                </div>
                                <div class="d-flex justify-content-between mb-1">
                                    <span class="text-muted">Booking Date:</span>
                                    <span class="text-dark">{{ b.booking_date ? b.booking_date.substring(0, 10) : '' }}</span>
                                </div>
                                <div class="d-flex justify-content-between pt-1 border-top">
                                    <span class="text-muted">Total Payable:</span>
                                    <strong class="text-success">₹{{ ((b.participants_count || 1) * ((b.trek && b.trek.price) || 0)).toLocaleString() }}</strong>
                                </div>
                            </div>

                            <!-- Actions Row -->
                            <div class="d-flex gap-2 pt-2 border-top mt-auto">
                                <button 
                                    v-if="b.payment_status !== 'Paid'" 
                                    @click="simulatePayment(b)" 
                                    class="btn btn-outline-success btn-sm flex-grow-1 fw-semibold"
                                >
                                    <i class="bi bi-credit-card me-1"></i>Pay Now
                                </button>
                                <button 
                                    @click="openCancelModal(b)" 
                                    class="btn btn-outline-danger btn-sm flex-grow-1 fw-semibold"
                                >
                                    <i class="bi bi-x-circle me-1"></i>Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: History (Completed & Cancelled) -->
        <div v-else>
            <div v-if="historyBookings.length === 0" class="card border-0 shadow-sm p-5 text-center text-muted rounded-3">
                <i class="bi bi-clock-history display-4 text-secondary mb-3 d-block"></i>
                <h5>No Past Reservations</h5>
                <p class="small text-muted mb-0">Completed or cancelled trek records will appear here.</p>
            </div>

            <div v-else class="card border-0 shadow-sm rounded-3 overflow-hidden">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light text-secondary text-uppercase small">
                            <tr>
                                <th>Booking ID</th>
                                <th>Expedition Trek</th>
                                <th>Dates</th>
                                <th>Participants</th>
                                <th>Payment</th>
                                <th class="text-end">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="h in historyBookings" :key="h.id">
                                <td class="fw-bold text-muted">#{{ h.id }}</td>
                                <td>
                                    <div class="fw-bold text-dark">{{ h.trek ? h.trek.name : 'Trek' }}</div>
                                    <small class="text-muted">{{ h.trek ? h.trek.location : '' }}</small>
                                </td>
                                <td class="small text-muted">
                                    {{ h.trek ? h.trek.start_date : '' }} to {{ h.trek ? h.trek.end_date : '' }}
                                </td>
                                <td>
                                    <span class="badge bg-light text-dark border">{{ h.participants_count }} trekker(s)</span>
                                </td>
                                <td>
                                    <span class="badge" :class="h.payment_status === 'Paid' ? 'bg-success' : 'bg-secondary'">
                                        {{ h.payment_status }}
                                    </span>
                                </td>
                                <td class="text-end">
                                    <span class="badge" :class="h.status === 'Completed' ? 'bg-success' : 'bg-danger'">
                                        {{ h.status }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Cancel Booking Confirmation Modal -->
        <div v-if="showCancelModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-exclamation-triangle-fill me-1"></i>Cancel Reservation
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="showCancelModal = false"></button>
                    </div>
                    <div class="modal-body p-4">
                        <p>Are you sure you want to cancel booking <strong>#{{ cancelTargetBooking ? cancelTargetBooking.id : '' }}</strong> for <strong>{{ cancelTargetBooking && cancelTargetBooking.trek ? cancelTargetBooking.trek.name : '' }}</strong>?</p>
                        <div class="alert alert-warning small mb-0">
                            <i class="bi bi-info-circle me-1"></i>
                            Your reserved slots ({{ cancelTargetBooking ? cancelTargetBooking.participants_count : 1 }} trekker spots) will be released back to the expedition available capacity.
                        </div>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" @click="showCancelModal = false">Keep Booking</button>
                        <button type="button" class="btn btn-danger btn-sm fw-bold" :disabled="cancelLoading" @click="confirmCancelBooking">
                            <span v-if="cancelLoading" class="spinner-border spinner-border-sm me-1"></span>
                            Yes, Cancel Reservation
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.MyBookings = MyBookings;

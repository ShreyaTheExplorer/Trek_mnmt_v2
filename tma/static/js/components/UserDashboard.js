/**
 * UserDashboard Component
 * Trekker Home Dashboard:
 * - Available treks count, my booked treks, and trek status breakdown
 * - Notifications panel with read/unread tracking and mark-as-read
 * - "Export booking history (CSV)" button with background job polling & download link
 */

const UserDashboard = {
    name: 'UserDashboard',
    data() {
        return {
            loading: true,
            dashboard: {
                available_treks_count: 0,
                booked_treks: [],
                status_counts: { Booked: 0, Completed: 0, Cancelled: 0 },
                total_bookings: 0
            },
            notifications: [],
            unreadCount: 0,

            // CSV Export Flow
            exportLoading: false,
            exportStatusMessage: '',
            exportReady: false,
            exportTaskId: null,
            exportDownloadUrl: null,
            exportFilename: null,
            exportPollTimer: null
        };
    },
    methods: {
        async fetchDashboardData() {
            this.loading = true;
            try {
                const [dashRes, notifRes] = await Promise.all([
                    window.tmaApi.get('/user/dashboard'),
                    window.tmaApi.get('/user/notifications')
                ]);

                if (dashRes && dashRes.data) {
                    this.dashboard = dashRes.data;
                }
                if (notifRes && notifRes.data) {
                    this.notifications = notifRes.data.notifications || [];
                    this.unreadCount = notifRes.data.unread_count || 0;
                }
            } catch (err) {
                window.showToast("Failed to load dashboard: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        async markAllRead() {
            try {
                await window.tmaApi.post('/user/notifications/read');
                this.unreadCount = 0;
                this.notifications.forEach(n => n.is_read = true);
                window.showToast("All notifications marked as read.", "success");
            } catch (err) {
                window.showToast("Could not mark notifications read: " + err.message, "danger");
            }
        },

        async triggerCsvExport() {
            this.exportLoading = true;
            this.exportReady = false;
            this.exportStatusMessage = "Export started... scheduling task.";
            this.exportDownloadUrl = null;
            this.exportFilename = null;

            try {
                const res = await window.tmaApi.post('/user/export');
                if (res && res.data) {
                    const taskId = res.data.task_id || res.data.job_id;
                    this.exportTaskId = taskId;
                    this.exportStatusMessage = "Export started... processing on Celery worker.";
                    window.showToast("Export started! We will notify you when it's ready.", "info");

                    // Poll task status endpoint
                    this.pollTaskStatus(taskId);
                }
            } catch (err) {
                this.exportLoading = false;
                window.showToast("Failed to start CSV export: " + err.message, "danger");
            }
        },

        pollTaskStatus(taskId) {
            if (this.exportPollTimer) clearInterval(this.exportPollTimer);

            let attempts = 0;
            this.exportPollTimer = setInterval(async () => {
                attempts++;
                try {
                    const [statusRes, notifRes] = await Promise.all([
                        window.tmaApi.get(`/user/export/${taskId}`),
                        window.tmaApi.get('/user/notifications')
                    ]);

                    // Refresh notifications panel in real-time
                    if (notifRes && notifRes.data) {
                        this.notifications = notifRes.data.notifications || [];
                        this.unreadCount = notifRes.data.unread_count || 0;
                    }

                    if (statusRes && statusRes.data) {
                        const { status, ready, download_url, filename } = statusRes.data;

                        if (ready || status === 'SUCCESS') {
                            clearInterval(this.exportPollTimer);
                            this.exportLoading = false;
                            this.exportReady = true;
                            this.exportDownloadUrl = download_url;
                            this.exportFilename = filename;
                            this.exportStatusMessage = "Export complete!";
                            window.showToast("Your booking history CSV is ready for download!", "success");
                        } else if (status === 'FAILURE') {
                            clearInterval(this.exportPollTimer);
                            this.exportLoading = false;
                            this.exportStatusMessage = "Task failed.";
                            window.showToast("Export task encountered an error.", "danger");
                        }
                    }
                } catch (err) {
                    if (attempts > 20) {
                        clearInterval(this.exportPollTimer);
                        this.exportLoading = false;
                        window.showToast("Polling timed out. Check your notifications.", "warning");
                    }
                }
            }, 1500);
        },

        async downloadExport() {
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
                window.showToast("Failed to download CSV: " + err.message, "danger");
            }
        }
    },
    mounted() {
        this.fetchDashboardData();
    },
    beforeUnmount() {
        if (this.exportPollTimer) clearInterval(this.exportPollTimer);
    },
    template: `
    <div class="container py-4">
        <!-- Title Banner -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-person-circle text-primary me-2"></i>Trekker Dashboard
                </h3>
                <p class="text-muted small mb-0">Overview of your mountain expeditions, real-time booking statuses, and in-app alerts.</p>
            </div>
            <div class="d-flex flex-wrap gap-2">
                <button @click="fetchDashboardData" class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1 shadow-sm">
                    <i class="bi bi-arrow-clockwise"></i> Refresh
                </button>
                <button 
                    @click="triggerCsvExport" 
                    class="btn btn-success btn-sm d-flex align-items-center gap-2 fw-semibold shadow-sm"
                    :disabled="exportLoading"
                >
                    <span v-if="exportLoading" class="spinner-border spinner-border-sm"></span>
                    <i v-else class="bi bi-file-earmark-spreadsheet-fill"></i>
                    <span>Export booking history (CSV)</span>
                </button>
            </div>
        </div>

        <!-- Export Progress / Notification Alert -->
        <div v-if="exportLoading || exportReady" class="card border-0 shadow-sm rounded-3 mb-4 border-start border-4 border-success">
            <div class="card-body p-3 d-flex flex-column flex-sm-row justify-content-between align-items-sm-center gap-3">
                <div class="d-flex align-items-center gap-2">
                    <div v-if="exportLoading" class="spinner-border spinner-border-sm text-success"></div>
                    <i v-else class="bi bi-check-circle-fill text-success fs-5"></i>
                    <div>
                        <strong class="text-dark">{{ exportReady ? 'Export Ready!' : 'Export Started' }}</strong>
                        <div class="small text-muted">{{ exportStatusMessage }}</div>
                    </div>
                </div>
                <div v-if="exportReady && exportDownloadUrl">
                    <button @click="downloadExport" class="btn btn-primary btn-sm px-3 fw-semibold">
                        <i class="bi bi-download me-1"></i>Download CSV
                    </button>
                </div>
            </div>
        </div>

        <!-- Metric KPI Cards -->
        <div class="row g-3 mb-4">
            <div class="col-6 col-md-3">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-primary h-100">
                    <div class="card-body p-3">
                        <span class="text-muted small fw-semibold text-uppercase">Active Bookings</span>
                        <h3 class="fw-bold text-dark mt-1 mb-0">{{ dashboard.status_counts.Booked || 0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-success h-100">
                    <div class="card-body p-3">
                        <span class="text-muted small fw-semibold text-uppercase">Completed Treks</span>
                        <h3 class="fw-bold text-dark mt-1 mb-0">{{ dashboard.status_counts.Completed || 0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-danger h-100">
                    <div class="card-body p-3">
                        <span class="text-muted small fw-semibold text-uppercase">Cancelled</span>
                        <h3 class="fw-bold text-dark mt-1 mb-0">{{ dashboard.status_counts.Cancelled || 0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card border-0 shadow-sm rounded-3 border-start border-4 border-info h-100">
                    <div class="card-body p-3">
                        <span class="text-muted small fw-semibold text-uppercase">Available Treks</span>
                        <h3 class="fw-bold text-dark mt-1 mb-0">{{ dashboard.available_treks_count || 0 }}</h3>
                    </div>
                </div>
            </div>
        </div>

        <!-- 2-Column Layout: My Booked Treks + Notifications Panel -->
        <div class="row g-4">
            <!-- Left: My Booked Treks -->
            <div class="col-12 col-lg-7">
                <div class="card border-0 shadow-sm rounded-3 h-100">
                    <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
                        <h5 class="fw-bold text-dark mb-0">
                            <i class="bi bi-calendar-check-fill text-primary me-2"></i>My Booked Treks
                        </h5>
                        <router-link to="/my-bookings" class="small fw-semibold text-decoration-none">
                            View All & History &raquo;
                        </router-link>
                    </div>
                    <div class="card-body p-3 pt-0">
                        <div v-if="loading" class="text-center py-4">
                            <div class="spinner-border spinner-border-sm text-primary"></div>
                        </div>
                        <div v-else-if="dashboard.booked_treks.length === 0" class="text-center py-4 text-muted">
                            <i class="bi bi-ticket-perforated fs-1 d-block mb-2"></i>
                            You currently have no active booked treks.
                            <div class="mt-3">
                                <router-link to="/treks" class="btn btn-outline-primary btn-sm">
                                    Browse Available Treks
                                </router-link>
                            </div>
                        </div>
                        <div v-else class="list-group list-group-flush">
                            <div v-for="b in dashboard.booked_treks" :key="b.id" class="list-group-item p-3 border rounded mb-2 bg-light">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <h6 class="fw-bold text-dark mb-1">{{ b.trek ? b.trek.name : 'Expedition Trek' }}</h6>
                                        <p class="text-muted small mb-2">
                                            <i class="bi bi-geo-alt me-1"></i>{{ b.trek ? b.trek.location : 'Himalayas' }} &bull;
                                            <i class="bi bi-calendar3 ms-1 me-1"></i>{{ b.trek ? b.trek.start_date : '' }}
                                        </p>
                                        <div class="small">
                                            <span class="text-muted">Enrolled: </span>
                                            <strong class="text-dark">{{ b.participants_count }} participant(s)</strong>
                                        </div>
                                    </div>
                                    <div class="text-end">
                                        <span class="badge" 
                                              :class="b.payment_status === 'Paid' ? 'bg-success' : 'bg-warning text-dark'">
                                            {{ b.payment_status }}
                                        </span>
                                        <div class="mt-2">
                                            <router-link to="/my-bookings" class="btn btn-primary btn-sm" style="font-size: 0.75rem;">
                                                Manage
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right: Notifications Panel -->
            <div class="col-12 col-lg-5">
                <div class="card border-0 shadow-sm rounded-3 h-100">
                    <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center gap-2">
                            <h5 class="fw-bold text-dark mb-0">
                                <i class="bi bi-bell-fill text-warning me-2"></i>Notifications
                            </h5>
                            <span v-if="unreadCount > 0" class="badge rounded-pill bg-danger small">
                                {{ unreadCount }} new
                            </span>
                        </div>
                        <button 
                            v-if="unreadCount > 0" 
                            @click="markAllRead" 
                            class="btn btn-link btn-sm text-decoration-none p-0 small"
                        >
                            Mark all read
                        </button>
                    </div>
                    <div class="card-body p-3 pt-0">
                        <div v-if="notifications.length === 0" class="text-center py-5 text-muted">
                            <i class="bi bi-bell-slash fs-2 d-block mb-2"></i>
                            No notifications yet.
                        </div>
                        <div v-else style="max-height: 380px; overflow-y: auto;">
                            <div v-for="n in notifications" :key="n.id" 
                                 class="p-3 mb-2 rounded border" 
                                 :class="n.is_read ? 'bg-light text-muted' : 'bg-white border-primary border-opacity-50 shadow-sm'">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    <small class="text-muted" style="font-size: 0.75rem;">
                                        {{ n.created_at ? n.created_at.substring(0, 16) : '' }}
                                    </small>
                                    <span v-if="!n.is_read" class="badge bg-primary" style="font-size: 0.65rem;">Unread</span>
                                </div>
                                <div class="small text-dark fw-medium">
                                    {{ n.message }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.UserDashboard = UserDashboard;


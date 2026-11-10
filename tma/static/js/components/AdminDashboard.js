/**
 * AdminDashboard Component
 * Key performance indicators, high-level metrics, and interactive Chart.js visualizations.
 */

const AdminDashboard = {
    name: 'AdminDashboard',
    data() {
        return {
            loading: true,
            dashboard: {
                total_treks: 0,
                total_users: 0,
                total_staff: 0,
                total_bookings: 0,
                treks_by_status: {},
                bookings_by_status: {}
            },
            stats: {
                popular_treks: [],
                bookings_per_month: [],
                users_participated: []
            },
            popularChart: null,
            trendsChart: null,
            statusChart: null,
            runningJob: false
        };
    },
    methods: {
        async fetchDashboardData() {
            this.loading = true;
            try {
                const [dashRes, statsRes] = await Promise.all([
                    window.tmaApi.get('/admin/dashboard'),
                    window.tmaApi.get('/admin/stats')
                ]);

                if (dashRes && dashRes.data) {
                    this.dashboard = dashRes.data;
                }
                if (statsRes && statsRes.data) {
                    this.stats = statsRes.data;
                }

                this.$nextTick(() => {
                    this.renderCharts();
                });
            } catch (err) {
                window.showToast("Failed to load dashboard metrics: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        renderCharts() {
            if (typeof Chart === 'undefined') {
                console.warn("Chart.js not loaded yet.");
                return;
            }

            // 1. Popular Treks Bar Chart
            const popCanvas = document.getElementById('popularTreksChart');
            if (popCanvas && this.stats.popular_treks) {
                if (this.popularChart) this.popularChart.destroy();

                const labels = this.stats.popular_treks.map(t => t.trek_name || 'Trek');
                const bookingCounts = this.stats.popular_treks.map(t => t.bookings || 0);
                const participantCounts = this.stats.popular_treks.map(t => t.participants || 0);

                this.popularChart = new Chart(popCanvas, {
                    type: 'bar',
                    data: {
                        labels: labels.length ? labels : ['No Treks Booked Yet'],
                        datasets: [
                            {
                                label: 'Bookings Count',
                                data: bookingCounts.length ? bookingCounts : [0],
                                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                                borderColor: 'rgba(54, 162, 235, 1)',
                                borderWidth: 1
                            },
                            {
                                label: 'Total Participants',
                                data: participantCounts.length ? participantCounts : [0],
                                backgroundColor: 'rgba(255, 159, 64, 0.7)',
                                borderColor: 'rgba(255, 159, 64, 1)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'top' },
                            title: { display: false }
                        },
                        scales: {
                            y: { beginAtZero: true, ticks: { precision: 0 } }
                        }
                    }
                });
            }

            // 2. Monthly Bookings & Revenue Line Chart
            const trendsCanvas = document.getElementById('monthlyTrendsChart');
            if (trendsCanvas && this.stats.bookings_per_month) {
                if (this.trendsChart) this.trendsChart.destroy();

                const months = this.stats.bookings_per_month.map(m => m.month);
                const counts = this.stats.bookings_per_month.map(m => m.count);
                const revenues = this.stats.bookings_per_month.map(m => m.revenue);

                this.trendsChart = new Chart(trendsCanvas, {
                    type: 'line',
                    data: {
                        labels: months.length ? months : ['Current Period'],
                        datasets: [
                            {
                                label: 'Bookings Volume',
                                data: counts.length ? counts : [0],
                                borderColor: '#0d6efd',
                                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                                fill: true,
                                tension: 0.3,
                                yAxisID: 'y'
                            },
                            {
                                label: 'Revenue (₹)',
                                data: revenues.length ? revenues : [0],
                                borderColor: '#198754',
                                backgroundColor: 'transparent',
                                borderDash: [5, 5],
                                tension: 0.3,
                                yAxisID: 'y1'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        scales: {
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                beginAtZero: true,
                                ticks: { precision: 0 },
                                title: { display: true, text: 'Bookings Count' }
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                beginAtZero: true,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'Revenue (₹)' }
                            }
                        }
                    }
                });
            }
        },

        async triggerJob(jobName) {
            this.runningJob = true;
            try {
                const res = await window.tmaApi.post(`/admin/jobs/${jobName}/run`);
                window.showToast(`Batch Job '${jobName}' triggered successfully!`, 'success');
                await this.fetchDashboardData();
            } catch (err) {
                window.showToast(`Failed to trigger '${jobName}': ` + err.message, 'danger');
            } finally {
                this.runningJob = false;
            }
        }
    },
    mounted() {
        this.fetchDashboardData();
    },
    beforeUnmount() {
        if (this.popularChart) this.popularChart.destroy();
        if (this.trendsChart) this.trendsChart.destroy();
        if (this.statusChart) this.statusChart.destroy();
    },
    template: `
    <div class="container-fluid py-4">
        <!-- Title Banner -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-speedometer2 text-primary me-2"></i>Admin Dashboard Overview
                </h3>
                <p class="text-muted small mb-0">System metrics, real-time booking statistics, and automated batch controls.</p>
            </div>
            <div class="d-flex gap-2">
                <button @click="fetchDashboardData" class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1">
                    <i class="bi bi-arrow-clockwise"></i> Refresh
                </button>
                <div class="dropdown">
                    <button class="btn btn-primary btn-sm dropdown-toggle d-flex align-items-center gap-1" 
                            type="button" data-bs-toggle="dropdown" :disabled="runningJob">
                        <i class="bi bi-gear-fill"></i> Trigger Batch Jobs
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end shadow">
                        <li>
                            <button @click="triggerJob('daily_reminders')" class="dropdown-item small">
                                <i class="bi bi-alarm me-2 text-warning"></i>Run Daily Reminders
                            </button>
                        </li>
                        <li>
                            <button @click="triggerJob('monthly_report')" class="dropdown-item small">
                                <i class="bi bi-file-earmark-bar-graph me-2 text-success"></i>Run Monthly Report
                            </button>
                        </li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- 4 High-Level Metric Stat Cards -->
        <div class="row g-3 mb-4">
            <!-- Total Treks -->
            <div class="col-12 col-sm-6 col-xl-3">
                <div class="card border-0 shadow-sm rounded-3 h-100 border-start border-4 border-primary">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="text-muted small fw-semibold text-uppercase">Total Treks</span>
                                <h2 class="fw-bold text-dark mt-1 mb-0">{{ dashboard.total_treks }}</h2>
                            </div>
                            <div class="p-3 bg-primary bg-opacity-10 text-primary rounded-circle">
                                <i class="bi bi-map-fill fs-3"></i>
                            </div>
                        </div>
                        <div class="mt-3 pt-2 border-top d-flex flex-wrap gap-1">
                            <span class="badge bg-success small">{{ dashboard.treks_by_status.Open || 0 }} Open</span>
                            <span class="badge bg-info text-dark small">{{ dashboard.treks_by_status.Approved || 0 }} Approved</span>
                            <span class="badge bg-secondary small">{{ dashboard.treks_by_status.Closed || 0 }} Closed</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Total Users -->
            <div class="col-12 col-sm-6 col-xl-3">
                <div class="card border-0 shadow-sm rounded-3 h-100 border-start border-4 border-success">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="text-muted small fw-semibold text-uppercase">Registered Trekkers</span>
                                <h2 class="fw-bold text-dark mt-1 mb-0">{{ dashboard.total_users }}</h2>
                            </div>
                            <div class="p-3 bg-success bg-opacity-10 text-success rounded-circle">
                                <i class="bi bi-people-fill fs-3"></i>
                            </div>
                        </div>
                        <div class="mt-3 pt-2 border-top small text-muted">
                            <i class="bi bi-check-circle text-success me-1"></i> Active user profiles
                        </div>
                    </div>
                </div>
            </div>

            <!-- Total Staff -->
            <div class="col-12 col-sm-6 col-xl-3">
                <div class="card border-0 shadow-sm rounded-3 h-100 border-start border-4 border-warning">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="text-muted small fw-semibold text-uppercase">Staff & Guides</span>
                                <h2 class="fw-bold text-dark mt-1 mb-0">{{ dashboard.total_staff }}</h2>
                            </div>
                            <div class="p-3 bg-warning bg-opacity-10 text-warning rounded-circle">
                                <i class="bi bi-person-badge-fill fs-3 text-dark"></i>
                            </div>
                        </div>
                        <div class="mt-3 pt-2 border-top small text-muted">
                            <i class="bi bi-shield-check text-warning me-1"></i> Expedition coordinators
                        </div>
                    </div>
                </div>
            </div>

            <!-- Total Bookings -->
            <div class="col-12 col-sm-6 col-xl-3">
                <div class="card border-0 shadow-sm rounded-3 h-100 border-start border-4 border-info">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="text-muted small fw-semibold text-uppercase">Total Bookings</span>
                                <h2 class="fw-bold text-dark mt-1 mb-0">{{ dashboard.total_bookings }}</h2>
                            </div>
                            <div class="p-3 bg-info bg-opacity-10 text-info rounded-circle">
                                <i class="bi bi-calendar-check-fill fs-3"></i>
                            </div>
                        </div>
                        <div class="mt-3 pt-2 border-top d-flex flex-wrap gap-1">
                            <span class="badge bg-primary small">{{ dashboard.bookings_by_status.Booked || 0 }} Active</span>
                            <span class="badge bg-success small">{{ dashboard.bookings_by_status.Completed || 0 }} Completed</span>
                            <span class="badge bg-danger small">{{ dashboard.bookings_by_status.Cancelled || 0 }} Cancelled</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Chart.js Visualization Grid -->
        <div class="row g-4">
            <!-- Popular Treks Bar Chart -->
            <div class="col-12 col-lg-6">
                <div class="card border-0 shadow-sm rounded-3 h-100">
                    <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
                        <h6 class="fw-bold mb-0 text-dark">
                            <i class="bi bi-bar-chart-fill text-primary me-2"></i>Most Popular Treks
                        </h6>
                        <span class="badge bg-light text-muted small">Top Bookings</span>
                    </div>
                    <div class="card-body pt-0">
                        <div class="chart-container" style="height: 320px;">
                            <canvas id="popularTreksChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Monthly Trends Line Chart -->
            <div class="col-12 col-lg-6">
                <div class="card border-0 shadow-sm rounded-3 h-100">
                    <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
                        <h6 class="fw-bold mb-0 text-dark">
                            <i class="bi bi-graph-up-arrow text-success me-2"></i>Monthly Bookings & Revenue Trend
                        </h6>
                        <span class="badge bg-light text-muted small">Timeline Activity</span>
                    </div>
                    <div class="card-body pt-0">
                        <div class="chart-container" style="height: 320px;">
                            <canvas id="monthlyTrendsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.AdminDashboard = AdminDashboard;


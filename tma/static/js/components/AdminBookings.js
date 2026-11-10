/**
 * AdminBookings Component
 * Complete audit ledger of all trekker reservations across active, completed, and cancelled states.
 */

const AdminBookings = {
    name: 'AdminBookings',
    data() {
        return {
            bookings: [],
            treks: [],
            loading: false,
            filterStatus: '',
            filterTrekId: '',
            searchQuery: ''
        };
    },
    computed: {
        filteredBookings() {
            let list = this.bookings;
            if (this.filterStatus) {
                list = list.filter(b => b.status === this.filterStatus);
            }
            if (this.filterTrekId) {
                list = list.filter(b => String(b.trek_id) === String(this.filterTrekId));
            }
            if (this.searchQuery) {
                const q = this.searchQuery.toLowerCase();
                list = list.filter(b => 
                    (b.user && (b.user.name.toLowerCase().includes(q) || b.user.email.toLowerCase().includes(q))) ||
                    (b.trek && (b.trek.name.toLowerCase().includes(q) || b.trek.location.toLowerCase().includes(q)))
                );
            }
            return list;
        }
    },
    methods: {
        async fetchBookings() {
            this.loading = true;
            try {
                const params = {};
                if (this.filterStatus) params.status = this.filterStatus;
                if (this.filterTrekId) params.trek_id = this.filterTrekId;

                const res = await window.tmaApi.get('/admin/bookings', params);
                if (res && res.data) {
                    this.bookings = res.data;
                }
            } catch (err) {
                window.showToast("Failed to fetch bookings ledger: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        async fetchTreksForFilter() {
            try {
                const res = await window.tmaApi.get('/admin/treks');
                if (res && res.data) {
                    this.treks = res.data;
                }
            } catch (err) {
                console.error("Could not load treks list for filter:", err);
            }
        }
    },
    mounted() {
        this.fetchBookings();
        this.fetchTreksForFilter();
    },
    template: `
    <div class="container-fluid py-4">
        <!-- Title Banner -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-journal-bookmark-fill text-primary me-2"></i>Global Bookings & History Ledger
                </h3>
                <p class="text-muted small mb-0">Auditable roster of reservations, payment confirmations, participant counts, and cancellation logs.</p>
            </div>
            <button @click="fetchBookings" class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1">
                <i class="bi bi-arrow-clockwise"></i> Refresh Ledger
            </button>
        </div>

        <!-- Filter Controls Card -->
        <div class="card border-0 shadow-sm rounded-3 mb-4">
            <div class="card-body p-3">
                <div class="row g-2 align-items-center">
                    <div class="col-12 col-md-5 col-lg-4">
                        <div class="input-group">
                            <span class="input-group-text bg-light text-muted border-end-0">
                                <i class="bi bi-search"></i>
                            </span>
                            <input 
                                type="text" 
                                v-model="searchQuery" 
                                class="form-control border-start-0" 
                                placeholder="Search by trekker or trek..." 
                            />
                        </div>
                    </div>
                    <div class="col-6 col-md-4 col-lg-3">
                        <select v-model="filterStatus" class="form-select" @change="fetchBookings">
                            <option value="">All Booking Statuses</option>
                            <option value="Booked">Booked (Active)</option>
                            <option value="Completed">Completed</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </div>
                    <div class="col-6 col-md-3 col-lg-3">
                        <select v-model="filterTrekId" class="form-select" @change="fetchBookings">
                            <option value="">All Treks</option>
                            <option v-for="t in treks" :key="t.id" :value="t.id">
                                {{ t.name }}
                            </option>
                        </select>
                    </div>
                    <div class="col-12 col-lg-2 text-lg-end text-muted small">
                        Showing <strong>{{ filteredBookings.length }}</strong> records
                    </div>
                </div>
            </div>
        </div>

        <!-- Responsive Bookings Table Card -->
        <div class="card border-0 shadow-sm rounded-3 overflow-hidden">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light text-secondary text-uppercase small">
                        <tr>
                            <th style="width: 50px;">ID</th>
                            <th>Trekker / Customer</th>
                            <th>Expedition Trek</th>
                            <th>Booking Date</th>
                            <th>Participants</th>
                            <th>Amount</th>
                            <th>Payment</th>
                            <th class="text-end">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="loading">
                            <td colspan="8" class="text-center py-5 text-muted">
                                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                                Loading booking records...
                            </td>
                        </tr>
                        <tr v-else-if="filteredBookings.length === 0">
                            <td colspan="8" class="text-center py-5 text-muted">
                                <i class="bi bi-inbox fs-2 d-block mb-2"></i>
                                No booking records found matching the filters.
                            </td>
                        </tr>
                        <tr v-for="b in filteredBookings" :key="b.id">
                            <td class="fw-bold text-muted">#{{ b.id }}</td>
                            <td>
                                <div class="fw-bold text-dark">{{ b.user ? b.user.name : 'Unknown User' }}</div>
                                <small class="text-muted">{{ b.user ? b.user.email : '' }}</small>
                            </td>
                            <td>
                                <div class="fw-semibold text-dark">{{ b.trek ? b.trek.name : 'Unknown Trek' }}</div>
                                <small class="text-muted"><i class="bi bi-geo-alt me-1"></i>{{ b.trek ? b.trek.location : '' }}</small>
                            </td>
                            <td class="small text-muted">
                                {{ b.booking_date ? b.booking_date.substring(0, 16) : 'N/A' }}
                            </td>
                            <td>
                                <span class="badge bg-light text-dark border">
                                    <i class="bi bi-people-fill text-primary me-1"></i>
                                    {{ b.participants_count }} trekker(s)
                                </span>
                            </td>
                            <td>
                                <span class="fw-bold text-success">
                                    ₹{{ ((b.participants_count || 1) * ((b.trek && b.trek.price) || 0)).toLocaleString() }}
                                </span>
                            </td>
                            <td>
                                <span class="badge" 
                                      :class="{
                                          'bg-success': b.payment_status === 'Paid',
                                          'bg-warning text-dark': b.payment_status === 'Pending',
                                          'bg-secondary': b.payment_status === 'NA'
                                      }">
                                    <i class="bi" :class="b.payment_status === 'Paid' ? 'bi-check-circle me-1' : 'bi-hourglass-split me-1'"></i>
                                    {{ b.payment_status }}
                                </span>
                            </td>
                            <td class="text-end">
                                <span class="badge" 
                                      :class="{
                                          'bg-primary': b.status === 'Booked',
                                          'bg-success': b.status === 'Completed',
                                          'bg-danger': b.status === 'Cancelled'
                                      }">
                                    {{ b.status }}
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `
};

window.AdminBookings = AdminBookings;


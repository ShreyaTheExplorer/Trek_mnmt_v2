/**
 * TrekkerCatalog Component
 * Exploration catalog of Himalayan treks with rich filters, pagination, and interactive booking modal.
 */

const TrekkerCatalog = {
    name: 'TrekkerCatalog',
    data() {
        return {
            treks: [],
            loading: false,
            pagination: {
                page: 1,
                per_page: 9,
                total: 0,
                pages: 1
            },
            filters: {
                q: '',
                location: '',
                difficulty: '',
                min_days: '',
                max_days: '',
                status: 'Open'
            },

            // Booking Modal State
            showBookingModal: false,
            selectedTrek: null,
            bookingForm: {
                participants_count: 1,
                agreedToTerms: false
            },
            bookingLoading: false,
            bookingSuccessData: null
        };
    },
    computed: {
        isLoggedIn() {
            return window.tmaApi.auth.isAuthenticated();
        },
        userRole() {
            return window.tmaApi.auth.role;
        },
        totalBookingCost() {
            if (!this.selectedTrek) return 0;
            return (this.bookingForm.participants_count || 1) * (this.selectedTrek.price || 0);
        }
    },
    methods: {
        async fetchTreks(page = 1) {
            this.loading = true;
            this.pagination.page = page;

            try {
                const params = {
                    page: this.pagination.page,
                    per_page: this.pagination.per_page
                };
                if (this.filters.q) params.q = this.filters.q;
                if (this.filters.location) params.location = this.filters.location;
                if (this.filters.difficulty) params.difficulty = this.filters.difficulty;
                if (this.filters.min_days) params.min_days = this.filters.min_days;
                if (this.filters.max_days) params.max_days = this.filters.max_days;
                if (this.filters.status) params.status = this.filters.status;

                const res = await window.tmaApi.get('/user/treks', params);
                if (res && res.data) {
                    this.treks = res.data.treks || [];
                    this.pagination = {
                        page: res.data.page || 1,
                        per_page: res.data.per_page || 9,
                        total: res.data.total || 0,
                        pages: res.data.pages || 1
                    };
                }
            } catch (err) {
                window.showToast("Could not load treks catalog: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        resetFilters() {
            this.filters = {
                q: '',
                location: '',
                difficulty: '',
                min_days: '',
                max_days: '',
                status: 'Open'
            };
            this.fetchTreks(1);
        },

        openBookingModal(trek) {
            if (!this.isLoggedIn) {
                window.showToast("Please log in to book this trek.", "warning");
                this.$router.push('/login');
                return;
            }
            if (this.userRole !== 'user') {
                window.showToast(`Only trekker accounts can make bookings. You are logged in as '${this.userRole}'.`, "warning");
                return;
            }
            if (trek.status !== 'Open' || trek.available_slots <= 0) {
                window.showToast("This trek is currently not accepting new bookings.", "warning");
                return;
            }

            this.selectedTrek = trek;
            this.bookingForm = {
                participants_count: 1,
                agreedToTerms: true
            };
            this.bookingSuccessData = null;
            this.showBookingModal = true;
        },

        async submitBooking() {
            if (!this.selectedTrek) return;

            const count = parseInt(this.bookingForm.participants_count);
            if (count < 1 || count > this.selectedTrek.available_slots) {
                window.showToast(`Please choose between 1 and ${this.selectedTrek.available_slots} participants.`, "warning");
                return;
            }

            this.bookingLoading = true;
            try {
                const res = await window.tmaApi.post('/user/bookings', {
                    trek_id: this.selectedTrek.id,
                    participants_count: count
                });

                if (res && res.data) {
                    this.bookingSuccessData = res.data;
                    window.showToast("Booking confirmed successfully!", "success");
                    // Refresh trek catalog so available slots update immediately
                    await this.fetchTreks(this.pagination.page);
                }
            } catch (err) {
                window.showToast("Booking failed: " + err.message, "danger");
            } finally {
                this.bookingLoading = false;
            }
        },

        async simulatePayment(bookingId) {
            try {
                await window.tmaApi.post(`/user/bookings/${bookingId}/pay`);
                window.showToast("Payment simulated successfully! Booking marked as Paid.", "success");
                if (this.bookingSuccessData && this.bookingSuccessData.booking) {
                    this.bookingSuccessData.booking.payment_status = 'Paid';
                }
            } catch (err) {
                window.showToast("Payment simulation failed: " + err.message, "danger");
            }
        }
    },
    mounted() {
        this.fetchTreks(1);
    },
    template: `
    <div class="container py-4">
        <!-- Hero Header -->
        <div class="p-4 p-md-5 mb-4 rounded-3 text-white shadow-sm" 
             style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);">
            <div class="col-md-9 px-0">
                <h1 class="display-5 fw-bold mb-2">Explore Himalayan Adventures</h1>
                <p class="lead mb-4 opacity-90">
                    Find and book verified mountain treks across Uttarakhand, Himachal Pradesh, Ladakh, and Sikkim. Led by certified mountaineering guides.
                </p>
                <div class="d-flex flex-wrap gap-2">
                    <span class="badge bg-light text-dark p-2"><i class="bi bi-shield-check text-success me-1"></i> Verified Guides</span>
                    <span class="badge bg-light text-dark p-2"><i class="bi bi-lightning-charge text-warning me-1"></i> Real-Time Slots</span>
                    <span class="badge bg-light text-dark p-2"><i class="bi bi-calendar2-check text-primary me-1"></i> Instant Confirmation</span>
                </div>
            </div>
        </div>

        <!-- Filter Search Bar -->
        <div class="card border-0 shadow-sm rounded-3 mb-4">
            <div class="card-body p-3 p-md-4">
                <form @submit.prevent="fetchTreks(1)">
                    <div class="row g-2 align-items-center">
                        <div class="col-12 col-md-4 col-lg-3">
                            <div class="input-group">
                                <span class="input-group-text bg-light text-muted border-end-0">
                                    <i class="bi bi-search"></i>
                                </span>
                                <input type="text" v-model="filters.q" class="form-control border-start-0" placeholder="Trek name or keywords..." />
                            </div>
                        </div>
                        <div class="col-6 col-md-3 col-lg-2">
                            <input type="text" v-model="filters.location" class="form-control" placeholder="Location..." />
                        </div>
                        <div class="col-6 col-md-3 col-lg-2">
                            <select v-model="filters.difficulty" class="form-select">
                                <option value="">All Difficulties</option>
                                <option value="Easy">Easy</option>
                                <option value="Moderate">Moderate</option>
                                <option value="Hard">Hard</option>
                            </select>
                        </div>
                        <div class="col-6 col-md-2 col-lg-2">
                            <select v-model="filters.status" class="form-select">
                                <option value="">All Treks</option>
                                <option value="Open">Open Only</option>
                                <option value="Approved">Approved</option>
                            </select>
                        </div>
                        <div class="col-6 col-md-4 col-lg-3 d-flex gap-2">
                            <button type="submit" class="btn btn-primary flex-grow-1">
                                <i class="bi bi-funnel me-1"></i>Filter
                            </button>
                            <button type="button" @click="resetFilters" class="btn btn-outline-secondary" title="Reset Filters">
                                <i class="bi bi-x-circle"></i>
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <div class="mt-2 text-muted small">Loading available trekking routes...</div>
        </div>

        <!-- Empty State -->
        <div v-else-if="treks.length === 0" class="card border-0 shadow-sm p-5 text-center text-muted">
            <i class="bi bi-compass display-4 mb-3 d-block text-secondary"></i>
            <h4>No Treks Available</h4>
            <p class="small text-muted mb-3">No expeditions found matching your filter criteria. Try clearing filters.</p>
            <div>
                <button @click="resetFilters" class="btn btn-outline-primary btn-sm">Reset All Filters</button>
            </div>
        </div>

        <!-- Trek Cards Grid -->
        <div v-else class="row g-4 mb-4">
            <div v-for="trek in treks" :key="trek.id" class="col-12 col-md-6 col-lg-4">
                <div class="card h-100 border-0 shadow-sm rounded-3 hover-shadow d-flex flex-column">
                    <!-- Card Top Ribbon -->
                    <div class="card-body p-4 d-flex flex-column">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="badge" :class="'badge-diff-' + trek.difficulty">
                                {{ trek.difficulty }}
                            </span>
                            <span class="badge" :class="'badge-status-' + trek.status">
                                {{ trek.status }}
                            </span>
                        </div>

                        <h5 class="fw-bold text-dark mb-1">{{ trek.name }}</h5>
                        <p class="text-muted small mb-3">
                            <i class="bi bi-geo-alt-fill text-danger me-1"></i>{{ trek.location }}
                        </p>

                        <p class="text-secondary small flex-grow-1 mb-3" style="min-height: 48px;">
                            {{ trek.description ? trek.description.substring(0, 110) + (trek.description.length > 110 ? '...' : '') : 'Experience scenic trails and alpine views.' }}
                        </p>

                        <!-- Highlights List -->
                        <div class="p-2 bg-light rounded small mb-3">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted"><i class="bi bi-clock me-1"></i>Duration:</span>
                                <strong class="text-dark">{{ trek.duration_days }} Days</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted"><i class="bi bi-calendar3 me-1"></i>Start Date:</span>
                                <strong class="text-dark">{{ trek.start_date }}</strong>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span class="text-muted"><i class="bi bi-people me-1"></i>Available Slots:</span>
                                <strong :class="trek.available_slots > 0 ? 'text-success' : 'text-danger'">
                                    {{ trek.available_slots }} / {{ trek.total_slots }}
                                </strong>
                            </div>
                        </div>

                        <!-- Card Footer Action -->
                        <div class="d-flex justify-content-between align-items-center pt-3 border-top mt-auto">
                            <div>
                                <span class="text-muted small d-block" style="font-size: 0.75rem;">Per Person</span>
                                <span class="fs-5 fw-bold text-success">₹{{ trek.price ? trek.price.toLocaleString() : 0 }}</span>
                            </div>

                            <button 
                                @click="openBookingModal(trek)" 
                                class="btn btn-primary btn-sm px-3 fw-semibold shadow-sm"
                                :disabled="trek.status !== 'Open' || trek.available_slots <= 0"
                            >
                                <i class="bi bi-ticket-perforated-fill me-1"></i>
                                {{ trek.available_slots <= 0 ? 'Fully Booked' : 'Book Now' }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Pagination Controls -->
        <div v-if="pagination.pages > 1" class="d-flex justify-content-center">
            <nav>
                <ul class="pagination pagination-sm">
                    <li class="page-item" :class="{ disabled: pagination.page <= 1 }">
                        <button class="page-link" @click="fetchTreks(pagination.page - 1)">&laquo; Prev</button>
                    </li>
                    <li v-for="p in pagination.pages" :key="p" class="page-item" :class="{ active: pagination.page === p }">
                        <button class="page-link" @click="fetchTreks(p)">{{ p }}</button>
                    </li>
                    <li class="page-item" :class="{ disabled: pagination.page >= pagination.pages }">
                        <button class="page-link" @click="fetchTreks(pagination.page + 1)">Next &raquo;</button>
                    </li>
                </ul>
            </nav>
        </div>

        <!-- Booking Modal -->
        <div v-if="showBookingModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-dark text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-compass text-warning me-2"></i>Book Trek: {{ selectedTrek ? selectedTrek.name : '' }}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" @click="showBookingModal = false"></button>
                    </div>

                    <!-- Step 1: Booking Form -->
                    <div v-if="!bookingSuccessData" class="modal-body p-4">
                        <div class="p-3 bg-light rounded mb-3 small">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted">Expedition Location:</span>
                                <strong class="text-dark">{{ selectedTrek.location }}</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted">Dates:</span>
                                <strong class="text-dark">{{ selectedTrek.start_date }} to {{ selectedTrek.end_date }} ({{ selectedTrek.duration_days }} Days)</strong>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span class="text-muted">Rate per Trekker:</span>
                                <strong class="text-success">₹{{ selectedTrek.price.toLocaleString() }}</strong>
                            </div>
                        </div>

                        <form @submit.prevent="submitBooking">
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Number of Participants *</label>
                                <input 
                                    type="number" 
                                    v-model="bookingForm.participants_count" 
                                    class="form-control form-control-lg text-center fw-bold" 
                                    min="1" 
                                    :max="selectedTrek.available_slots" 
                                    required 
                                />
                                <div class="form-text small text-muted text-center">
                                    Maximum available slots for this trek: <strong>{{ selectedTrek.available_slots }}</strong>
                                </div>
                            </div>

                            <div class="p-3 bg-primary bg-opacity-10 rounded border border-primary border-opacity-25 text-center mb-3">
                                <span class="small text-muted d-block">Estimated Total Amount</span>
                                <span class="fs-3 fw-bold text-primary">₹{{ totalBookingCost.toLocaleString() }}</span>
                            </div>

                            <div class="form-check mb-3">
                                <input class="form-check-input" type="checkbox" id="termsCheck" v-model="bookingForm.agreedToTerms" required>
                                <label class="form-check-label small text-muted" for="termsCheck">
                                    I confirm that all participants are physically fit and agree to adhere to high-altitude safety guidelines.
                                </label>
                            </div>

                            <button 
                                type="submit" 
                                class="btn btn-warning text-dark fw-bold w-100 py-2 d-flex justify-content-center align-items-center gap-2"
                                :disabled="bookingLoading || !bookingForm.agreedToTerms"
                            >
                                <span v-if="bookingLoading" class="spinner-border spinner-border-sm"></span>
                                <span>{{ bookingLoading ? 'Confirming Reservation...' : 'Confirm Reservation' }}</span>
                            </button>
                        </form>
                    </div>

                    <!-- Step 2: Confirmation & Payment Simulation -->
                    <div v-else class="modal-body p-4 text-center">
                        <div class="text-success mb-3">
                            <i class="bi bi-check-circle-fill display-4"></i>
                        </div>
                        <h4 class="fw-bold text-dark">Booking Confirmed!</h4>
                        <p class="text-muted small">
                            Your reservation #{{ bookingSuccessData.booking.id }} for <strong>{{ selectedTrek.name }}</strong> has been registered.
                        </p>

                        <div class="p-3 bg-light rounded text-start small mb-3">
                            <div class="d-flex justify-content-between mb-1">
                                <span>Booking ID:</span>
                                <strong>#{{ bookingSuccessData.booking.id }}</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span>Participants:</span>
                                <strong>{{ bookingSuccessData.booking.participants_count }} Trekkers</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span>Payment Status:</span>
                                <span class="badge" :class="bookingSuccessData.booking.payment_status === 'Paid' ? 'bg-success' : 'bg-warning text-dark'">
                                    {{ bookingSuccessData.booking.payment_status }}
                                </span>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span>Total Payable:</span>
                                <strong class="text-success">₹{{ totalBookingCost.toLocaleString() }}</strong>
                            </div>
                        </div>

                        <div class="d-flex gap-2 justify-content-center">
                            <button 
                                v-if="bookingSuccessData.booking.payment_status !== 'Paid'"
                                @click="simulatePayment(bookingSuccessData.booking.id)" 
                                class="btn btn-success btn-sm px-3"
                            >
                                <i class="bi bi-credit-card me-1"></i>Simulate Payment (Pay Now)
                            </button>
                            <router-link to="/my-bookings" class="btn btn-primary btn-sm px-3" @click="showBookingModal = false">
                                <i class="bi bi-journal-bookmark me-1"></i>View in My Bookings
                            </router-link>
                        </div>
                    </div>

                    <div class="modal-footer bg-light p-2">
                        <button type="button" class="btn btn-secondary btn-sm" @click="showBookingModal = false">Close</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.TrekkerCatalog = TrekkerCatalog;


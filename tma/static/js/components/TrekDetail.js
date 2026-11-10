/**
 * TrekDetail Component
 * Comprehensive expedition page:
 * - Full metadata, route description, packing instructions, real-time slots
 * - Participants count input with validation (1 to available_slots)
 * - Book button (disabled unless Open and slots > 0)
 * - Optional "Pay (simulated)" button upon booking
 */

const TrekDetail = {
    name: 'TrekDetail',
    data() {
        return {
            trekId: null,
            trek: null,
            loading: true,
            bookingLoading: false,
            payingLoading: false,
            errorMessage: '',

            // Booking Form
            participantsCount: 1,
            confirmedBooking: null
        };
    },
    computed: {
        isLoggedIn() {
            return window.tmaApi.auth.isAuthenticated();
        },
        userRole() {
            return window.tmaApi.auth.role;
        },
        totalCost() {
            if (!this.trek) return 0;
            return (parseInt(this.participantsCount) || 1) * (this.trek.price || 0);
        },
        canBook() {
            return this.trek && this.trek.status === 'Open' && this.trek.available_slots > 0;
        }
    },
    methods: {
        async fetchTrekDetail() {
            this.loading = true;
            this.errorMessage = '';
            this.trekId = this.$route.params.id;

            try {
                const res = await window.tmaApi.get(`/user/treks/${this.trekId}`);
                if (res && res.data) {
                    this.trek = res.data;
                    this.participantsCount = 1;
                }
            } catch (err) {
                this.errorMessage = err.message || "Failed to load trek details.";
                window.showToast(this.errorMessage, "danger");
            } finally {
                this.loading = false;
            }
        },

        async submitBooking() {
            if (!this.isLoggedIn) {
                window.showToast("Please sign in as a trekker to book.", "warning");
                this.$router.push('/login');
                return;
            }
            if (this.userRole !== 'user') {
                window.showToast(`Only trekker accounts can book. You are signed in as '${this.userRole}'.`, "warning");
                return;
            }

            const count = parseInt(this.participantsCount);
            if (isNaN(count) || count < 1 || count > this.trek.available_slots) {
                window.showToast(`Please enter a valid participant count between 1 and ${this.trek.available_slots}.`, "warning");
                return;
            }

            this.bookingLoading = true;
            try {
                const res = await window.tmaApi.post('/user/bookings', {
                    trek_id: parseInt(this.trekId),
                    participants_count: count
                });

                if (res && res.data) {
                    this.confirmedBooking = res.data.booking || res.data;
                    if (res.data.trek && res.data.trek.available_slots !== undefined) {
                        this.trek.available_slots = res.data.trek.available_slots;
                    } else {
                        this.trek.available_slots = Math.max(0, this.trek.available_slots - count);
                    }
                    window.showToast("Booking confirmed successfully!", "success");
                }
            } catch (err) {
                window.showToast("Booking failed: " + err.message, "danger");
            } finally {
                this.bookingLoading = false;
            }
        },

        async simulatePayment() {
            if (!this.confirmedBooking) return;
            this.payingLoading = true;
            try {
                const res = await window.tmaApi.post(`/user/bookings/${this.confirmedBooking.id}/pay`);
                if (res && res.data) {
                    this.confirmedBooking.payment_status = 'Paid';
                    window.showToast("Payment simulated successfully! Booking status updated to Paid.", "success");
                }
            } catch (err) {
                window.showToast("Payment simulation failed: " + err.message, "danger");
            } finally {
                this.payingLoading = false;
            }
        }
    },
    mounted() {
        this.fetchTrekDetail();
    },
    template: `
    <div class="container py-4">
        <!-- Back Navigation -->
        <div class="mb-3">
            <router-link to="/treks" class="btn btn-outline-secondary btn-sm d-inline-flex align-items-center gap-1">
                <i class="bi bi-arrow-left"></i> Back to Trek Explorer
            </router-link>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <div class="mt-2 text-muted small">Loading expedition details...</div>
        </div>

        <!-- Error State -->
        <div v-else-if="errorMessage" class="card border-danger border-2 p-4 text-center my-4">
            <i class="bi bi-exclamation-triangle-fill display-4 text-danger mb-2"></i>
            <h4 class="text-danger fw-bold">Expedition Not Found</h4>
            <p class="text-muted">{{ errorMessage }}</p>
            <div>
                <router-link to="/treks" class="btn btn-primary btn-sm">Return to Catalog</router-link>
            </div>
        </div>

        <!-- Trek Details Main Content -->
        <div v-else-if="trek" class="row g-4">
            <!-- Left 8 Columns: Trek Information -->
            <div class="col-12 col-lg-8">
                <div class="card border-0 shadow-sm rounded-3 overflow-hidden mb-4">
                    <!-- Banner -->
                    <div class="p-4 text-white" style="background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%);">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="badge" :class="'badge-diff-' + trek.difficulty">{{ trek.difficulty }}</span>
                            <span class="badge" :class="trek.status === 'Open' ? 'badge-status-Open' : 'badge-status-Closed'">
                                {{ trek.status }}
                            </span>
                        </div>
                        <h2 class="fw-bold mb-1">{{ trek.name }}</h2>
                        <p class="mb-0 opacity-90"><i class="bi bi-geo-alt-fill text-danger me-1"></i>{{ trek.location }}</p>
                    </div>

                    <div class="card-body p-4">
                        <!-- Key Highlights Grid -->
                        <div class="row g-3 mb-4">
                            <div class="col-6 col-sm-3">
                                <div class="p-3 bg-light rounded text-center">
                                    <div class="text-muted small">Duration</div>
                                    <div class="fw-bold text-dark fs-5">{{ trek.duration_days }} Days</div>
                                </div>
                            </div>
                            <div class="col-6 col-sm-3">
                                <div class="p-3 bg-light rounded text-center">
                                    <div class="text-muted small">Price / Trekker</div>
                                    <div class="fw-bold text-success fs-5">₹{{ trek.price.toLocaleString() }}</div>
                                </div>
                            </div>
                            <div class="col-6 col-sm-3">
                                <div class="p-3 bg-light rounded text-center">
                                    <div class="text-muted small">Slots Left</div>
                                    <div class="fw-bold fs-5" :class="trek.available_slots > 0 ? 'text-primary' : 'text-danger'">
                                        {{ trek.available_slots }} / {{ trek.total_slots }}
                                    </div>
                                </div>
                            </div>
                            <div class="col-6 col-sm-3">
                                <div class="p-3 bg-light rounded text-center">
                                    <div class="text-muted small">Start Date</div>
                                    <div class="fw-bold text-dark fs-6 mt-1">{{ trek.start_date }}</div>
                                </div>
                            </div>
                        </div>

                        <!-- Full Description -->
                        <h5 class="fw-bold text-dark mb-2">
                            <i class="bi bi-info-circle-fill text-primary me-2"></i>About This Expedition
                        </h5>
                        <p class="text-secondary mb-4" style="line-height: 1.7;">
                            {{ trek.description || 'No description provided.' }}
                        </p>

                        <!-- Instructions -->
                        <h5 class="fw-bold text-dark mb-2">
                            <i class="bi bi-backpack-fill text-warning me-2"></i>Preparation & Gear Instructions
                        </h5>
                        <div class="p-3 bg-light rounded border small text-dark mb-3">
                            {{ trek.instructions || 'Bring sturdy trekking shoes, warm layers, water purification, and emergency personal medicines.' }}
                        </div>

                        <!-- Schedule Dates -->
                        <div class="small text-muted">
                            <i class="bi bi-calendar3 me-1"></i>Expedition Window: <strong>{{ trek.start_date }}</strong> to <strong>{{ trek.end_date }}</strong>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right 4 Columns: Booking Card & Payment Simulator -->
            <div class="col-12 col-lg-4">
                <!-- If NOT booked yet: Booking Box -->
                <div v-if="!confirmedBooking" class="card border-0 shadow-sm rounded-3 sticky-top" style="top: 80px;">
                    <div class="card-header bg-white py-3 border-0">
                        <h5 class="fw-bold text-dark mb-0">
                            <i class="bi bi-ticket-perforated-fill text-primary me-2"></i>Reserve Your Slots
                        </h5>
                    </div>
                    <div class="card-body p-4 pt-0">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span class="text-muted small">Per Person Fee</span>
                            <span class="fs-4 fw-bold text-success">₹{{ trek.price.toLocaleString() }}</span>
                        </div>

                        <!-- Slots availability badge -->
                        <div class="mb-3">
                            <span class="badge w-100 py-2" :class="canBook ? 'bg-success bg-opacity-10 text-success border border-success' : 'bg-danger bg-opacity-10 text-danger border border-danger'">
                                <i class="bi" :class="canBook ? 'bi-check-circle me-1' : 'bi-x-circle me-1'"></i>
                                {{ canBook ? trek.available_slots + ' slots currently available' : (trek.status !== 'Open' ? 'Registration Closed' : 'Expedition Fully Booked') }}
                            </span>
                        </div>

                        <form @submit.prevent="submitBooking">
                            <!-- Participants Count Input -->
                            <div class="mb-3">
                                <label class="form-label small fw-semibold text-secondary">Number of Participants *</label>
                                <input 
                                    type="number" 
                                    v-model="participantsCount" 
                                    class="form-control form-control-lg text-center fw-bold" 
                                    min="1" 
                                    :max="trek.available_slots || 1" 
                                    :disabled="!canBook"
                                    required 
                                />
                                <div class="form-text small text-muted text-center">
                                    Min 1, Max {{ trek.available_slots }}
                                </div>
                            </div>

                            <!-- Cost Calculation -->
                            <div class="p-3 bg-light rounded text-center mb-3">
                                <div class="small text-muted">Total Payable Amount</div>
                                <div class="fs-3 fw-bold text-dark">₹{{ totalCost.toLocaleString() }}</div>
                            </div>

                            <!-- Book Button: disabled unless trek is Open and has slots -->
                            <button 
                                type="submit" 
                                class="btn btn-primary w-100 py-2 fw-semibold shadow-sm d-flex justify-content-center align-items-center gap-2"
                                :disabled="!canBook || bookingLoading"
                            >
                                <span v-if="bookingLoading" class="spinner-border spinner-border-sm"></span>
                                <span>{{ !canBook ? 'Booking Unavailable' : (bookingLoading ? 'Processing Booking...' : 'Book Expedition') }}</span>
                            </button>
                        </form>

                        <div v-if="!isLoggedIn" class="mt-3 text-center small text-muted">
                            <router-link to="/login">Sign in</router-link> to confirm your reservation.
                        </div>
                    </div>
                </div>

                <!-- If ALREADY confirmed booking: Success & Payment Simulation Card -->
                <div v-else class="card border-0 shadow-sm rounded-3 border-top border-4 border-success">
                    <div class="card-body p-4 text-center">
                        <div class="text-success mb-2">
                            <i class="bi bi-check-circle-fill display-4"></i>
                        </div>
                        <h4 class="fw-bold text-dark mb-1">Booking Confirmed!</h4>
                        <p class="text-muted small mb-3">
                            Reservation <strong>#{{ confirmedBooking.id }}</strong> has been recorded.
                        </p>

                        <div class="p-3 bg-light rounded text-start small mb-3">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted">Enrolled Trekkers:</span>
                                <strong>{{ confirmedBooking.participants_count }} Person(s)</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted">Payment Status:</span>
                                <span class="badge" :class="confirmedBooking.payment_status === 'Paid' ? 'bg-success' : 'bg-warning text-dark'">
                                    {{ confirmedBooking.payment_status }}
                                </span>
                            </div>
                            <div class="d-flex justify-content-between pt-1 border-top">
                                <span class="text-muted">Total Paid / Payable:</span>
                                <strong class="text-success">₹{{ (confirmedBooking.participants_count * trek.price).toLocaleString() }}</strong>
                            </div>
                        </div>

                        <!-- Optional Pay (simulated) button -->
                        <div class="d-grid gap-2">
                            <button 
                                v-if="confirmedBooking.payment_status !== 'Paid'" 
                                @click="simulatePayment" 
                                class="btn btn-success fw-semibold d-flex justify-content-center align-items-center gap-2"
                                :disabled="payingLoading"
                            >
                                <span v-if="payingLoading" class="spinner-border spinner-border-sm"></span>
                                <i v-else class="bi bi-credit-card-fill"></i>
                                <span>Pay (Simulated)</span>
                            </button>

                            <router-link to="/my-bookings" class="btn btn-outline-primary btn-sm">
                                <i class="bi bi-journal-bookmark me-1"></i>View in My Bookings
                            </router-link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.TrekDetail = TrekDetail;

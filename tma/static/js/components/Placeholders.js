/**
 * Temporary / Base Placeholders for Trekker & Staff routes
 * Will be fully expanded in subsequent parts.
 */

const TrekkerCatalogPlaceholder = {
    name: 'TrekkerCatalog',
    data() {
        return {
            treks: [],
            loading: false
        };
    },
    async mounted() {
        this.loading = true;
        try {
            const res = await window.tmaApi.get('/user/treks');
            if (res && res.data) {
                this.treks = res.data.treks || [];
            }
        } catch (e) {
            console.error(e);
        } finally {
            this.loading = false;
        }
    },
    template: `
    <div class="container py-5">
        <div class="text-center mb-5">
            <h2 class="fw-bold">Explore Himalayan Expeditions</h2>
            <p class="text-muted">Discover breathtaking trekking destinations across India</p>
        </div>
        <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary"></div>
        </div>
        <div v-else class="row g-4">
            <div v-for="t in treks" :key="t.id" class="col-12 col-md-6 col-lg-4">
                <div class="card h-100 shadow-sm border-0 rounded-3">
                    <div class="card-body">
                        <span class="badge" :class="'badge-diff-' + t.difficulty">{{ t.difficulty }}</span>
                        <h5 class="fw-bold mt-2">{{ t.name }}</h5>
                        <p class="text-muted small"><i class="bi bi-geo-alt me-1"></i>{{ t.location }}</p>
                        <p class="small text-secondary">{{ t.description }}</p>
                        <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                            <span class="fw-bold text-success fs-5">₹{{ t.price.toLocaleString() }}</span>
                            <span class="badge bg-light text-dark border">{{ t.available_slots }} slots left</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

const StaffDashboardPlaceholder = {
    name: 'StaffDashboard',
    template: `
    <div class="container py-5 text-center">
        <i class="bi bi-person-workspace display-3 text-warning mb-3 d-block"></i>
        <h3>Staff Operations Portal</h3>
        <p class="text-muted">Assigned expeditions, participants rosters, and slot updates module.</p>
    </div>
    `
};

const MyBookingsPlaceholder = {
    name: 'MyBookings',
    template: `
    <div class="container py-5 text-center">
        <i class="bi bi-journal-bookmark display-3 text-primary mb-3 d-block"></i>
        <h3>My Bookings & History</h3>
        <p class="text-muted">View confirmed reservations, payment receipts, and CSV exports.</p>
    </div>
    `
};

const ProfilePlaceholder = {
    name: 'ProfileView',
    data() {
        return {
            user: window.tmaApi.auth.user || {}
        };
    },
    template: `
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card shadow-sm border-0 p-4">
                    <h4 class="fw-bold mb-3"><i class="bi bi-person-circle me-2"></i>User Profile</h4>
                    <ul class="list-group list-group-flush mb-3">
                        <li class="list-group-item d-flex justify-content-between">
                            <strong>Name:</strong> <span>{{ user.name }}</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between">
                            <strong>Email:</strong> <span>{{ user.email }}</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between">
                            <strong>Role:</strong> <span class="badge bg-warning text-dark text-capitalize">{{ user.role }}</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    `
};

window.TrekkerCatalogPlaceholder = TrekkerCatalogPlaceholder;
window.StaffDashboardPlaceholder = StaffDashboardPlaceholder;
window.MyBookingsPlaceholder = MyBookingsPlaceholder;
window.ProfilePlaceholder = ProfilePlaceholder;


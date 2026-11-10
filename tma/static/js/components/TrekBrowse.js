/**
 * TrekBrowse Component
 * Explorer portal for finding treks with search box, multi-parameter filters (difficulty, location, duration),
 * paginated trek cards displaying slots left and Open/Closed status, with Book disabled unless Open and slots > 0.
 */

const TrekBrowse = {
    name: 'TrekBrowse',
    data() {
        return {
            treks: [],
            loading: false,
            searchQuery: '',
            filterLocation: '',
            filterDifficulty: '',
            filterMinDays: '',
            filterMaxDays: '',
            pagination: {
                page: 1,
                per_page: 9,
                total: 0,
                pages: 1
            }
        };
    },
    computed: {
        isLoggedIn() {
            return window.tmaApi.auth.isAuthenticated();
        },
        userRole() {
            return window.tmaApi.auth.role;
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
                if (this.searchQuery) params.q = this.searchQuery;
                if (this.filterLocation) params.location = this.filterLocation;
                if (this.filterDifficulty) params.difficulty = this.filterDifficulty;
                if (this.filterMinDays) params.min_days = this.filterMinDays;
                if (this.filterMaxDays) params.max_days = this.filterMaxDays;

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
                window.showToast("Failed to load treks: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        resetFilters() {
            this.searchQuery = '';
            this.filterLocation = '';
            this.filterDifficulty = '';
            this.filterMinDays = '';
            this.filterMaxDays = '';
            this.fetchTreks(1);
        },

        goToDetail(trekId) {
            this.$router.push(`/treks/${trekId}`);
        }
    },
    mounted() {
        this.fetchTreks(1);
    },
    template: `
    <div class="container py-4">
        <!-- Explorer Header -->
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
                <h3 class="fw-bold mb-1 text-dark">
                    <i class="bi bi-compass text-primary me-2"></i>Explore Himalayan Expeditions
                </h3>
                <p class="text-muted small mb-0">Browse scheduled alpine treks, compare trail difficulty, and reserve your spots.</p>
            </div>
            <div class="text-muted small">
                Showing <strong>{{ treks.length }}</strong> expeditions (Page {{ pagination.page }} of {{ pagination.pages || 1 }})
            </div>
        </div>

        <!-- Search Box & Filter Controls Card -->
        <div class="card border-0 shadow-sm rounded-3 mb-4">
            <div class="card-body p-3 p-md-4">
                <form @submit.prevent="fetchTreks(1)">
                    <div class="row g-2 align-items-center">
                        <!-- Search Box -->
                        <div class="col-12 col-md-4 col-lg-3">
                            <div class="input-group">
                                <span class="input-group-text bg-light text-muted border-end-0">
                                    <i class="bi bi-search"></i>
                                </span>
                                <input 
                                    type="text" 
                                    v-model="searchQuery" 
                                    class="form-control border-start-0" 
                                    placeholder="Search trek name..." 
                                />
                            </div>
                        </div>

                        <!-- Location Filter -->
                        <div class="col-6 col-md-3 col-lg-2">
                            <input 
                                type="text" 
                                v-model="filterLocation" 
                                class="form-control" 
                                placeholder="Location (e.g. Ladakh)..." 
                            />
                        </div>

                        <!-- Difficulty Dropdown -->
                        <div class="col-6 col-md-2 col-lg-2">
                            <select v-model="filterDifficulty" class="form-select">
                                <option value="">All Difficulties</option>
                                <option value="Easy">Easy</option>
                                <option value="Moderate">Moderate</option>
                                <option value="Hard">Hard</option>
                            </select>
                        </div>

                        <!-- Duration Range -->
                        <div class="col-6 col-md-3 col-lg-3">
                            <div class="input-group">
                                <input type="number" v-model="filterMinDays" class="form-control" placeholder="Min Days" min="1" />
                                <span class="input-group-text bg-light text-muted">-</span>
                                <input type="number" v-model="filterMaxDays" class="form-control" placeholder="Max Days" min="1" />
                            </div>
                        </div>

                        <!-- Action Buttons -->
                        <div class="col-6 col-md-12 col-lg-2 d-flex gap-2">
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
            <div class="mt-2 text-muted small">Loading trekking catalog...</div>
        </div>

        <!-- Empty State -->
        <div v-else-if="treks.length === 0" class="card border-0 shadow-sm p-5 text-center text-muted rounded-3">
            <i class="bi bi-binoculars display-4 text-secondary mb-3 d-block"></i>
            <h4>No Expeditions Found</h4>
            <p class="small text-muted mb-3">No treks matched your search criteria. Try broadening your filters.</p>
            <div>
                <button @click="resetFilters" class="btn btn-outline-primary btn-sm">Clear Filters</button>
            </div>
        </div>

        <!-- Paginated Trek Cards Grid -->
        <div v-else class="row g-4 mb-4">
            <div v-for="t in treks" :key="t.id" class="col-12 col-md-6 col-lg-4">
                <div class="card h-100 border-0 shadow-sm rounded-3 hover-shadow d-flex flex-column">
                    <div class="card-body p-4 d-flex flex-column">
                        <!-- Top Badges: Difficulty & Open/Closed Status -->
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="badge" :class="'badge-diff-' + t.difficulty">
                                {{ t.difficulty }}
                            </span>
                            <!-- Open / Closed Badge -->
                            <span class="badge" 
                                  :class="t.status === 'Open' ? 'badge-status-Open' : 'badge-status-Closed'">
                                <i class="bi" :class="t.status === 'Open' ? 'bi-door-open-fill me-1' : 'bi-door-closed-fill me-1'"></i>
                                {{ t.status === 'Open' ? 'Open' : 'Closed' }}
                            </span>
                        </div>

                        <!-- Trek Title & Location -->
                        <h5 class="fw-bold text-dark mb-1">{{ t.name }}</h5>
                        <p class="text-muted small mb-3">
                            <i class="bi bi-geo-alt-fill text-danger me-1"></i>{{ t.location }}
                        </p>

                        <!-- Description Snippet -->
                        <p class="text-secondary small flex-grow-1 mb-3" style="min-height: 48px;">
                            {{ t.description ? (t.description.length > 110 ? t.description.substring(0, 110) + '...' : t.description) : 'Scenic Himalayan trek trail.' }}
                        </p>

                        <!-- Slots Left & Details Banner -->
                        <div class="p-3 bg-light rounded small mb-3">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted"><i class="bi bi-clock me-1"></i>Duration:</span>
                                <strong class="text-dark">{{ t.duration_days }} Days</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted"><i class="bi bi-calendar3 me-1"></i>Dates:</span>
                                <strong class="text-dark">{{ t.start_date }} to {{ t.end_date }}</strong>
                            </div>
                            <div class="d-flex justify-content-between pt-1 border-top">
                                <span class="text-muted"><i class="bi bi-people me-1"></i>Slots Left:</span>
                                <!-- Slots Left Highlight -->
                                <strong :class="t.available_slots > 0 ? 'text-success' : 'text-danger'">
                                    {{ t.available_slots > 0 ? t.available_slots + ' slots left' : 'Fully Booked' }}
                                </strong>
                            </div>
                        </div>

                        <!-- Card Footer Actions: Book & Details -->
                        <div class="d-flex justify-content-between align-items-center pt-3 border-top mt-auto">
                            <div>
                                <span class="text-muted small d-block" style="font-size: 0.75rem;">Price per person</span>
                                <span class="fs-5 fw-bold text-success">₹{{ t.price ? t.price.toLocaleString() : 0 }}</span>
                            </div>

                            <div class="btn-group">
                                <button 
                                    @click="goToDetail(t.id)" 
                                    class="btn btn-outline-primary btn-sm"
                                    title="View Full Details"
                                >
                                    Details
                                </button>
                                <!-- "Book" is disabled unless the trek is Open and has slots -->
                                <button 
                                    @click="goToDetail(t.id)" 
                                    class="btn btn-primary btn-sm fw-semibold"
                                    :disabled="t.status !== 'Open' || t.available_slots <= 0"
                                    :title="t.status !== 'Open' ? 'Trek registration is Closed' : (t.available_slots <= 0 ? 'No slots left' : 'Book expedition')"
                                >
                                    <i class="bi bi-ticket-perforated-fill me-1"></i>Book
                                </button>
                            </div>
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
    </div>
    `
};

window.TrekBrowse = TrekBrowse;


/**
 * AdminSearch Component
 * Unified search portal across treks, staff guides, and registered users.
 */

const AdminSearch = {
    name: 'AdminSearch',
    data() {
        return {
            query: '',
            searchType: '',
            loading: false,
            hasSearched: false,
            results: {
                treks: [],
                staff: [],
                users: []
            }
        };
    },
    methods: {
        async performSearch() {
            if (!this.query.trim()) {
                window.showToast("Please enter a search query.", "warning");
                return;
            }
            this.loading = true;
            this.hasSearched = true;
            try {
                const params = { q: this.query.trim() };
                if (this.searchType) params.type = this.searchType;

                const res = await window.tmaApi.get('/admin/search', params);
                if (res && res.data) {
                    this.results = {
                        treks: res.data.treks || [],
                        staff: res.data.staff || [],
                        users: res.data.users || []
                    };
                }
            } catch (err) {
                window.showToast("Search failed: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
    <div class="container-fluid py-4">
        <!-- Title Banner -->
        <div class="mb-4">
            <h3 class="fw-bold mb-1 text-dark">
                <i class="bi bi-search text-primary me-2"></i>Global Administrative Search
            </h3>
            <p class="text-muted small mb-0">Search across the entire platform ecosystem for treks, mountain guides, and user accounts.</p>
        </div>

        <!-- Search Bar Input Card -->
        <div class="card border-0 shadow-sm rounded-3 mb-4">
            <div class="card-body p-4">
                <form @submit.prevent="performSearch">
                    <div class="row g-2">
                        <div class="col-12 col-md-7 col-lg-8">
                            <div class="input-group input-group-lg">
                                <span class="input-group-text bg-white border-end-0 text-muted">
                                    <i class="bi bi-search"></i>
                                </span>
                                <input 
                                    type="text" 
                                    v-model="query" 
                                    class="form-control border-start-0" 
                                    placeholder="Enter keywords (e.g. Kedarkantha, Uttarakhand, Dave, Alice)..." 
                                    required 
                                />
                            </div>
                        </div>
                        <div class="col-6 col-md-3 col-lg-2">
                            <select v-model="searchType" class="form-select form-select-lg">
                                <option value="">All Categories</option>
                                <option value="treks">Treks Only</option>
                                <option value="staff">Staff Only</option>
                                <option value="users">Users Only</option>
                            </select>
                        </div>
                        <div class="col-6 col-md-2 col-lg-2">
                            <button type="submit" class="btn btn-primary btn-lg w-100 fw-semibold" :disabled="loading">
                                <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                                {{ loading ? 'Searching...' : 'Search' }}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Initial Placeholder -->
        <div v-if="!hasSearched" class="text-center py-5 text-muted">
            <i class="bi bi-binoculars display-4 text-secondary mb-3 d-block"></i>
            <h5>Find Anything in Seconds</h5>
            <p class="small text-muted">Type any trek title, mountain range, guide name, or user email address above.</p>
        </div>

        <!-- Search Results Breakdown -->
        <div v-else>
            <div v-if="loading" class="text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
                <div class="mt-2 text-muted small">Scanning database records...</div>
            </div>

            <div v-else-if="results.treks.length === 0 && results.staff.length === 0 && results.users.length === 0" 
                 class="card border-0 shadow-sm p-5 text-center text-muted">
                <i class="bi bi-emoji-neutral fs-1 mb-2"></i>
                <h5>No Matching Records Found</h5>
                <p class="small text-muted mb-0">No records found matching "<strong>{{ query }}</strong>". Try broader keywords.</p>
            </div>

            <div v-else class="row g-4">
                <!-- Treks Results -->
                <div v-if="!searchType || searchType === 'treks'" class="col-12">
                    <div class="card border-0 shadow-sm rounded-3">
                        <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
                            <h6 class="fw-bold mb-0 text-dark">
                                <i class="bi bi-map-fill text-primary me-2"></i>Matching Treks ({{ results.treks.length }})
                            </h6>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover align-middle mb-0">
                                <thead class="table-light small text-secondary">
                                    <tr>
                                        <th>ID</th>
                                        <th>Trek Name</th>
                                        <th>Location</th>
                                        <th>Difficulty</th>
                                        <th>Slots Available</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-if="results.treks.length === 0">
                                        <td colspan="6" class="text-center py-3 text-muted small">No treks matched.</td>
                                    </tr>
                                    <tr v-for="t in results.treks" :key="t.id">
                                        <td>#{{ t.id }}</td>
                                        <td class="fw-bold">{{ t.name }}</td>
                                        <td>{{ t.location }}</td>
                                        <td><span class="badge" :class="'badge-diff-' + t.difficulty">{{ t.difficulty }}</span></td>
                                        <td>{{ t.available_slots }} / {{ t.total_slots }}</td>
                                        <td><span class="badge" :class="'badge-status-' + t.status">{{ t.status }}</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Staff Results -->
                <div v-if="!searchType || searchType === 'staff'" class="col-12 col-lg-6">
                    <div class="card border-0 shadow-sm rounded-3 h-100">
                        <div class="card-header bg-white py-3 border-0">
                            <h6 class="fw-bold mb-0 text-dark">
                                <i class="bi bi-person-workspace text-warning me-2"></i>Matching Staff Guides ({{ results.staff.length }})
                            </h6>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover align-middle mb-0">
                                <thead class="table-light small text-secondary">
                                    <tr>
                                        <th>Staff Name</th>
                                        <th>Specialization</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-if="results.staff.length === 0">
                                        <td colspan="3" class="text-center py-3 text-muted small">No staff guides matched.</td>
                                    </tr>
                                    <tr v-for="s in results.staff" :key="s.id">
                                        <td>
                                            <div class="fw-bold">{{ s.name }}</div>
                                            <small class="text-muted">{{ s.email }}</small>
                                        </td>
                                        <td>{{ s.specialization || 'Guide' }}</td>
                                        <td>
                                            <span class="badge" 
                                                  :class="{
                                                      'bg-success': s.status === 'active',
                                                      'bg-warning text-dark': s.status === 'inactive',
                                                      'bg-danger': s.status === 'blacklisted'
                                                  }">
                                                {{ s.status }}
                                            </span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Users Results -->
                <div v-if="!searchType || searchType === 'users'" class="col-12 col-lg-6">
                    <div class="card border-0 shadow-sm rounded-3 h-100">
                        <div class="card-header bg-white py-3 border-0">
                            <h6 class="fw-bold mb-0 text-dark">
                                <i class="bi bi-people-fill text-success me-2"></i>Matching Trekkers ({{ results.users.length }})
                            </h6>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover align-middle mb-0">
                                <thead class="table-light small text-secondary">
                                    <tr>
                                        <th>User Name</th>
                                        <th>Phone</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-if="results.users.length === 0">
                                        <td colspan="3" class="text-center py-3 text-muted small">No users matched.</td>
                                    </tr>
                                    <tr v-for="u in results.users" :key="u.id">
                                        <td>
                                            <div class="fw-bold">{{ u.name }}</div>
                                            <small class="text-muted">{{ u.email }}</small>
                                        </td>
                                        <td>{{ u.phone || 'N/A' }}</td>
                                        <td>
                                            <span class="badge" 
                                                  :class="{
                                                      'bg-success': u.status === 'active',
                                                      'bg-warning text-dark': u.status === 'inactive',
                                                      'bg-danger': u.status === 'blacklisted'
                                                  }">
                                                {{ u.status }}
                                            </span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.AdminSearch = AdminSearch;


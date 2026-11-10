/**
 * LoginPage Component
 * Handles unified authentication for Admin, Staff, and User accounts.
 */

const LoginPage = {
    name: 'LoginPage',
    data() {
        return {
            email: '',
            password: '',
            loading: false,
            errorMessage: '',
            successMessage: ''
        };
    },
    methods: {
        async handleLogin() {
            this.loading = true;
            this.errorMessage = '';
            this.successMessage = '';

            try {
                const res = await window.tmaApi.post('/auth/login', {
                    email: this.email,
                    password: this.password
                });

                if (res && res.data) {
                    const { token, role, name } = res.data;
                    const userObj = { name, email: this.email, role };
                    window.tmaApi.auth.setAuth(token, role, userObj);

                    window.showToast(`Welcome back, ${name}! Logged in as ${role}.`, 'success');

                    // Role-based redirection
                    if (role === 'admin') {
                        this.$router.push('/admin');
                    } else if (role === 'staff') {
                        this.$router.push('/staff');
                    } else {
                        this.$router.push('/treks');
                    }
                }
            } catch (err) {
                this.errorMessage = err.message || "Login failed. Please check your credentials.";
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-12 col-sm-10 col-md-8 col-lg-5">
                <div class="card shadow-sm border-0 rounded-3">
                    <div class="card-body p-4 p-sm-5">
                        <div class="text-center mb-4">
                            <div class="brand-icon-wrapper rounded-circle d-inline-flex align-items-center justify-content-center p-3 mb-3 shadow-sm" style="width: 58px; height: 58px;">
                                <i class="bi bi-compass-fill fs-2"></i>
                            </div>
                            <h3 class="fw-bold text-dark">Welcome to Boundless<span class="text-peach">Treks</span></h3>
                            <p class="text-muted small">Sign in to manage your alpine expeditions & reservations</p>
                        </div>

                        <!-- Alert feedback -->
                        <div v-if="errorMessage" class="alert alert-danger d-flex align-items-center gap-2 py-2 small" role="alert">
                            <i class="bi bi-exclamation-triangle-fill flex-shrink-0"></i>
                            <div>{{ errorMessage }}</div>
                        </div>

                        <form @submit.prevent="handleLogin" novalidate>
                            <div class="mb-3">
                                <label for="loginEmail" class="form-label small fw-semibold text-secondary">Email Address</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light text-muted border-end-0">
                                        <i class="bi bi-envelope"></i>
                                    </span>
                                    <input 
                                        type="email" 
                                        id="loginEmail" 
                                        v-model="email" 
                                        class="form-control border-start-0" 
                                        placeholder="name@example.com" 
                                        required 
                                        autocomplete="email"
                                    />
                                </div>
                            </div>

                            <div class="mb-4">
                                <label for="loginPassword" class="form-label small fw-semibold text-secondary">Password</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light text-muted border-end-0">
                                        <i class="bi bi-key"></i>
                                    </span>
                                    <input 
                                        type="password" 
                                        id="loginPassword" 
                                        v-model="password" 
                                        class="form-control border-start-0" 
                                        placeholder="Enter your password" 
                                        required 
                                        autocomplete="current-password"
                                    />
                                </div>
                            </div>

                            <button 
                                type="submit" 
                                class="btn btn-primary w-100 py-2 fw-semibold d-flex justify-content-center align-items-center gap-2"
                                :disabled="loading || !email || !password"
                            >
                                <span v-if="loading" class="spinner-border spinner-border-sm" role="status"></span>
                                <span>{{ loading ? 'Signing in...' : 'Sign In' }}</span>
                            </button>
                        </form>

                        <div class="mt-4 pt-3 border-top text-center">
                            <span class="text-muted small">Don't have an account yet? </span>
                            <router-link to="/register" class="text-decoration-none small fw-semibold">
                                Register as Trekker
                            </router-link>
                        </div>

                        <!-- Demo credentials hint for testing -->
                        <div class="mt-4 p-3 bg-light rounded small text-muted">
                            <div class="fw-bold mb-1"><i class="bi bi-info-circle me-1"></i>Seed Accounts:</div>
                            <div><strong>Admin:</strong> <code>admin@tma.com</code> / <code>admin123</code></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.LoginPage = LoginPage;


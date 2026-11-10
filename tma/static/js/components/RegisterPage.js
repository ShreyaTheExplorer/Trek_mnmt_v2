/**
 * RegisterPage Component
 * Self-registration portal for trekkers with HTML5 form validation.
 */

const RegisterPage = {
    name: 'RegisterPage',
    data() {
        return {
            form: {
                name: '',
                email: '',
                password: '',
                confirmPassword: '',
                phone: '',
                age: null,
                emergency_contact: '',
                address: ''
            },
            loading: false,
            errorMessage: '',
            successMessage: ''
        };
    },
    methods: {
        async handleRegister() {
            this.errorMessage = '';
            this.successMessage = '';

            // Password confirmation check
            if (this.form.password !== this.form.confirmPassword) {
                this.errorMessage = "Passwords do not match.";
                return;
            }

            this.loading = true;

            try {
                const payload = {
                    name: this.form.name,
                    email: this.form.email,
                    password: this.form.password,
                    phone: this.form.phone,
                    age: this.form.age ? parseInt(this.form.age) : null,
                    emergency_contact: this.form.emergency_contact || null,
                    address: this.form.address || null
                };

                const res = await window.tmaApi.post('/auth/register', payload);

                if (res && res.data) {
                    const { token, role, user } = res.data;
                    window.tmaApi.auth.setAuth(token, role, user);
                    window.showToast("Registration successful! Welcome to BoundlessTreks.", "success");
                    this.$router.push('/treks');
                }
            } catch (err) {
                this.errorMessage = err.message || "Registration failed. Please check your inputs.";
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-12 col-md-10 col-lg-7">
                <div class="card shadow-sm border-0 rounded-3">
                    <div class="card-body p-4 p-sm-5">
                        <div class="text-center mb-4">
                            <div class="brand-icon-wrapper rounded-circle d-inline-flex align-items-center justify-content-center p-3 mb-3 shadow-sm" style="width: 58px; height: 58px;">
                                <i class="bi bi-person-plus-fill fs-2"></i>
                            </div>
                            <h3 class="fw-bold text-dark">Join Boundless<span class="text-peach">Treks</span></h3>
                            <p class="text-muted small">Create your account to explore and book certified wilderness expeditions</p>
                        </div>

                        <!-- Feedback alerts -->
                        <div v-if="errorMessage" class="alert alert-danger d-flex align-items-center gap-2 py-2 small" role="alert">
                            <i class="bi bi-exclamation-triangle-fill flex-shrink-0"></i>
                            <div>{{ errorMessage }}</div>
                        </div>

                        <form @submit.prevent="handleRegister">
                            <div class="row g-3">
                                <!-- Full Name -->
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Full Name *</label>
                                    <input 
                                        type="text" 
                                        v-model="form.name" 
                                        class="form-control" 
                                        placeholder="e.g. John Doe" 
                                        required 
                                    />
                                </div>

                                <!-- Email -->
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Email Address *</label>
                                    <input 
                                        type="email" 
                                        v-model="form.email" 
                                        class="form-control" 
                                        placeholder="name@example.com" 
                                        required 
                                    />
                                </div>

                                <!-- Phone Number with HTML5 Pattern -->
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Phone Number *</label>
                                    <input 
                                        type="tel" 
                                        v-model="form.phone" 
                                        class="form-control" 
                                        placeholder="e.g. +91 9876543210" 
                                        pattern="^\\+?[0-9\\s\\-]{7,20}$"
                                        title="Phone number must be 7-20 digits, optionally starting with '+'"
                                        required 
                                    />
                                    <div class="form-text small">7 to 20 digits, spaces or hyphens allowed.</div>
                                </div>

                                <!-- Age -->
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Age</label>
                                    <input 
                                        type="number" 
                                        v-model="form.age" 
                                        class="form-control" 
                                        placeholder="e.g. 26" 
                                        min="12" 
                                        max="100" 
                                    />
                                </div>

                                <!-- Password (minlength 6) -->
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Password *</label>
                                    <input 
                                        type="password" 
                                        v-model="form.password" 
                                        class="form-control" 
                                        placeholder="Minimum 6 characters" 
                                        minlength="6" 
                                        required 
                                        autocomplete="new-password"
                                    />
                                    <div class="form-text small">Must be at least 6 characters.</div>
                                </div>

                                <!-- Confirm Password -->
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Confirm Password *</label>
                                    <input 
                                        type="password" 
                                        v-model="form.confirmPassword" 
                                        class="form-control" 
                                        placeholder="Re-enter password" 
                                        minlength="6" 
                                        required 
                                        autocomplete="new-password"
                                    />
                                </div>

                                <!-- Emergency Contact -->
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Emergency Contact Phone</label>
                                    <input 
                                        type="tel" 
                                        v-model="form.emergency_contact" 
                                        class="form-control" 
                                        placeholder="Guardian / Emergency contact" 
                                    />
                                </div>

                                <!-- Address -->
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Residential Address</label>
                                    <input 
                                        type="text" 
                                        v-model="form.address" 
                                        class="form-control" 
                                        placeholder="City, State" 
                                    />
                                </div>
                            </div>

                            <button 
                                type="submit" 
                                class="btn btn-warning text-dark fw-semibold w-100 py-2 mt-4 d-flex justify-content-center align-items-center gap-2"
                                :disabled="loading"
                            >
                                <span v-if="loading" class="spinner-border spinner-border-sm" role="status"></span>
                                <span>{{ loading ? 'Creating Account...' : 'Complete Registration' }}</span>
                            </button>
                        </form>

                        <div class="mt-4 pt-3 border-top text-center">
                            <span class="text-muted small">Already have an account? </span>
                            <router-link to="/login" class="text-decoration-none small fw-semibold">
                                Sign In
                            </router-link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.RegisterPage = RegisterPage;


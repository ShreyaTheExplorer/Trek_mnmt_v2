/**
 * ProfileView Component
 * User profile management:
 * - View & update personal information (name, phone, age, emergency contact, address)
 * - Password change form with client-side validation
 */

const ProfileView = {
    name: 'ProfileView',
    data() {
        return {
            loading: true,
            saving: false,
            userProfile: {
                name: '',
                email: '',
                phone: '',
                age: null,
                emergency_contact: '',
                address: '',
                role: '',
                status: ''
            },
            passwordForm: {
                current_password: '',
                new_password: '',
                confirm_new_password: ''
            },
            profileError: '',
            passwordError: ''
        };
    },
    methods: {
        async fetchProfile() {
            this.loading = true;
            try {
                const res = await window.tmaApi.get('/auth/me');
                if (res && res.data) {
                    this.userProfile = {
                        name: res.data.name || '',
                        email: res.data.email || '',
                        phone: res.data.phone || '',
                        age: res.data.age || null,
                        emergency_contact: res.data.emergency_contact || '',
                        address: res.data.address || '',
                        role: res.data.role || '',
                        status: res.data.status || 'active'
                    };
                }
            } catch (err) {
                window.showToast("Failed to load profile: " + err.message, "danger");
            } finally {
                this.loading = false;
            }
        },

        async updateProfileInfo() {
            this.saving = true;
            this.profileError = '';
            try {
                const payload = {
                    name: this.userProfile.name,
                    phone: this.userProfile.phone,
                    age: this.userProfile.age ? parseInt(this.userProfile.age) : null,
                    emergency_contact: this.userProfile.emergency_contact || null,
                    address: this.userProfile.address || null
                };

                const res = await window.tmaApi.put('/auth/me', payload);
                if (res && res.data) {
                    window.tmaApi.auth.setAuth(
                        window.tmaApi.auth.token,
                        window.tmaApi.auth.role,
                        res.data.user || res.data
                    );
                    window.showToast("Profile information updated successfully!", "success");
                }
            } catch (err) {
                this.profileError = err.message || "Could not update profile.";
                window.showToast(this.profileError, "danger");
            } finally {
                this.saving = false;
            }
        },

        async changePassword() {
            this.passwordError = '';
            if (!this.passwordForm.current_password) {
                this.passwordError = "Please enter your current password.";
                return;
            }
            if (!this.passwordForm.new_password || this.passwordForm.new_password.length < 6) {
                this.passwordError = "New password must be at least 6 characters.";
                return;
            }
            if (this.passwordForm.new_password !== this.passwordForm.confirm_new_password) {
                this.passwordError = "New passwords do not match.";
                return;
            }

            this.saving = true;
            try {
                await window.tmaApi.put('/auth/me', {
                    current_password: this.passwordForm.current_password,
                    password: this.passwordForm.new_password
                });
                window.showToast("Password updated successfully!", "success");
                this.passwordForm = {
                    current_password: '',
                    new_password: '',
                    confirm_new_password: ''
                };
            } catch (err) {
                this.passwordError = err.message || "Failed to change password.";
                window.showToast(this.passwordError, "danger");
            } finally {
                this.saving = false;
            }
        }
    },
    mounted() {
        this.fetchProfile();
    },
    template: `
    <div class="container py-4">
        <!-- Title Banner -->
        <div class="mb-4">
            <h3 class="fw-bold mb-1 text-dark">
                <i class="bi bi-person-gear text-primary me-2"></i>My Profile & Account Settings
            </h3>
            <p class="text-muted small mb-0">Update contact phone numbers, emergency details, and login credentials.</p>
        </div>

        <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <div class="mt-2 text-muted small">Loading profile details...</div>
        </div>

        <div v-else class="row g-4">
            <!-- Left Column: Personal Information Form -->
            <div class="col-12 col-lg-8">
                <div class="card border-0 shadow-sm rounded-3">
                    <div class="card-header bg-white py-3 border-0 d-flex justify-content-between align-items-center">
                        <h5 class="fw-bold text-dark mb-0">
                            <i class="bi bi-person-circle text-primary me-2"></i>Personal Details
                        </h5>
                        <span class="badge bg-warning text-dark text-capitalize px-3 py-2">
                            Role: {{ userProfile.role }}
                        </span>
                    </div>
                    <div class="card-body p-4 pt-0">
                        <div v-if="profileError" class="alert alert-danger small py-2 d-flex align-items-center gap-2 mb-3">
                            <i class="bi bi-exclamation-triangle-fill"></i>
                            <div>{{ profileError }}</div>
                        </div>

                        <form @submit.prevent="updateProfileInfo">
                            <div class="row g-3">
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Full Name *</label>
                                    <input type="text" v-model="userProfile.name" class="form-control" required />
                                </div>
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Email Address</label>
                                    <input type="email" :value="userProfile.email" class="form-control bg-light" readonly />
                                    <div class="form-text small" style="font-size: 0.75rem;">Email cannot be changed.</div>
                                </div>

                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Contact Phone *</label>
                                    <input type="tel" v-model="userProfile.phone" class="form-control" required />
                                </div>
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Age</label>
                                    <input type="number" v-model="userProfile.age" class="form-control" min="12" max="100" />
                                </div>

                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Emergency Contact Phone</label>
                                    <input type="tel" v-model="userProfile.emergency_contact" class="form-control" placeholder="Guardian / Relative contact" />
                                </div>
                                <div class="col-12 col-md-6">
                                    <label class="form-label small fw-semibold text-secondary">Residential Address</label>
                                    <input type="text" v-model="userProfile.address" class="form-control" placeholder="City, State" />
                                </div>
                            </div>

                            <div class="mt-4 pt-3 border-top d-flex justify-content-end">
                                <button type="submit" class="btn btn-primary px-4 fw-semibold" :disabled="saving">
                                    <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
                                    Save Profile Changes
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>

            <!-- Right Column: Security & Password Update -->
            <div class="col-12 col-lg-4">
                <div class="card border-0 shadow-sm rounded-3">
                    <div class="card-header bg-white py-3 border-0">
                        <h5 class="fw-bold text-dark mb-0">
                            <i class="bi bi-shield-lock text-warning me-2"></i>Change Password
                        </h5>
                    </div>
                    <div class="card-body p-4 pt-0">
                        <div v-if="passwordError" class="alert alert-danger small py-2 d-flex align-items-center gap-2 mb-3">
                            <i class="bi bi-exclamation-triangle-fill"></i>
                            <div>{{ passwordError }}</div>
                        </div>

                        <form @submit.prevent="changePassword">
                            <div class="mb-3">
                                <label class="form-label small fw-semibold text-secondary">New Password</label>
                                <input type="password" v-model="passwordForm.new_password" class="form-control" minlength="6" placeholder="Min 6 characters" required />
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold text-secondary">Confirm New Password</label>
                                <input type="password" v-model="passwordForm.confirm_new_password" class="form-control" minlength="6" placeholder="Re-type new password" required />
                            </div>

                            <button type="submit" class="btn btn-warning text-dark fw-semibold w-100" :disabled="saving">
                                <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
                                Update Password
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `
};

window.ProfileView = ProfileView;

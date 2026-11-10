/**
 * Main Vue 3 Application Mount
 * Mounts Vue application, integrates Vue Router, and registers global components.
 * Branded for BoundlessTreks with comprehensive, realistic footer.
 */

document.addEventListener('DOMContentLoaded', () => {
    const { createApp } = Vue;

    const app = createApp({
        components: {
            'navbar-component': window.NavbarComponent,
            'toast-component': window.ToastComponent
        },
        template: `
        <div id="tma-app-root" class="d-flex flex-column min-vh-100">
            <!-- Global Floating Toast Notification Alerts -->
            <toast-component />

            <!-- Dynamic Role-Aware Navigation Bar -->
            <navbar-component />

            <!-- Main Route Outlet -->
            <main class="flex-grow-1">
                <router-view />
            </main>

            <!-- Realistic Multi-Column BoundlessTreks Footer -->
            <footer class="boundless-footer mt-auto text-white">
                <!-- Top Trust & Safety Strip -->
                <div class="footer-top-strip py-3 border-bottom border-white-10">
                    <div class="container">
                        <div class="row g-3 text-center text-md-start align-items-center">
                            <div class="col-12 col-md-4 d-flex align-items-center justify-content-center justify-content-md-start gap-2">
                                <i class="bi bi-shield-check fs-4 text-peach"></i>
                                <div>
                                    <div class="fw-semibold text-white small">Certified IMF & UIAA Mountain Guides</div>
                                    <div class="text-white-50" style="font-size: 0.75rem;">100% wilderness first-aid qualified leaders</div>
                                </div>
                            </div>
                            <div class="col-12 col-md-4 d-flex align-items-center justify-content-center gap-2">
                                <i class="bi bi-tree fs-4 text-orchid"></i>
                                <div>
                                    <div class="fw-semibold text-white small">Eco-Certified Leave No Trace Partner</div>
                                    <div class="text-white-50" style="font-size: 0.75rem;">Zero-waste alpine trail conservation</div>
                                </div>
                            </div>
                            <div class="col-12 col-md-4 d-flex align-items-center justify-content-center justify-content-md-end gap-2">
                                <i class="bi bi-broadcast-pin fs-4 text-peach"></i>
                                <div>
                                    <div class="fw-semibold text-white small">24/7 Expedition Radio Support</div>
                                    <div class="text-white-50" style="font-size: 0.75rem;">Satellite & VHF basecamp emergency links</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Main Footer Navigation & Basecamp Details -->
                <div class="container py-5">
                    <div class="row g-4">
                        <!-- Brand Column -->
                        <div class="col-12 col-lg-4">
                            <div class="d-flex align-items-center gap-2 mb-3">
                                <div class="brand-icon-wrapper rounded-circle d-flex align-items-center justify-content-center shadow-sm">
                                    <i class="bi bi-compass-fill"></i>
                                </div>
                                <span class="fs-4 fw-bold text-white">Boundless<span class="text-peach">Treks</span></span>
                            </div>
                            <p class="text-white-50 small pe-lg-3 mb-3">
                                BoundlessTreks is India's premier alpine expedition and wilderness management platform. We craft safe, sustainable, and transformative summit journeys across the Greater Himalayas, Western Ghats, and remote global trails.
                            </p>
                            <div class="d-flex gap-2">
                                <a href="javascript:void(0)" class="social-icon-btn" title="Instagram"><i class="bi bi-instagram"></i></a>
                                <a href="javascript:void(0)" class="social-icon-btn" title="YouTube"><i class="bi bi-youtube"></i></a>
                                <a href="javascript:void(0)" class="social-icon-btn" title="Facebook"><i class="bi bi-facebook"></i></a>
                                <a href="javascript:void(0)" class="social-icon-btn" title="Strava"><i class="bi bi-strava"></i></a>
                                <a href="javascript:void(0)" class="social-icon-btn" title="Twitter/X"><i class="bi bi-twitter-x"></i></a>
                            </div>
                        </div>

                        <!-- Quick Navigation Links -->
                        <div class="col-6 col-md-3 col-lg-2">
                            <h6 class="text-uppercase fw-bold text-peach mb-3 small tracking-wider">Explore Treks</h6>
                            <ul class="list-unstyled small mb-0 d-flex flex-column gap-2">
                                <li><router-link to="/treks" class="footer-link">All Expeditions</router-link></li>
                                <li><router-link to="/treks" class="footer-link">Winter Summit Trails</router-link></li>
                                <li><router-link to="/treks" class="footer-link">Glacial Pass Crossings</router-link></li>
                                <li><router-link to="/treks" class="footer-link">Alpine Meadows & Lakes</router-link></li>
                                <li><router-link to="/treks" class="footer-link">Weekend High-Ridges</router-link></li>
                            </ul>
                        </div>

                        <!-- Expedition Support & Safety -->
                        <div class="col-6 col-md-3 col-lg-3">
                            <h6 class="text-uppercase fw-bold text-peach mb-3 small tracking-wider">Safety & Support</h6>
                            <ul class="list-unstyled small mb-0 d-flex flex-column gap-2">
                                <li><a href="javascript:void(0)" class="footer-link">High Altitude Protocol (AMS)</a></li>
                                <li><a href="javascript:void(0)" class="footer-link">Packing & Gear Checklists</a></li>
                                <li><a href="javascript:void(0)" class="footer-link">Weather & Snow Advisories</a></li>
                                <li><a href="javascript:void(0)" class="footer-link">Forest Permits & Regulations</a></li>
                                <li><a href="javascript:void(0)" class="footer-link">Cancellation & Refund Policy</a></li>
                            </ul>
                        </div>

                        <!-- Basecamp & Contact Info -->
                        <div class="col-12 col-md-6 col-lg-3">
                            <h6 class="text-uppercase fw-bold text-peach mb-3 small tracking-wider">Basecamp Headquarters</h6>
                            <ul class="list-unstyled small mb-0 d-flex flex-column gap-2 text-white-50">
                                <li class="d-flex align-items-start gap-2">
                                    <i class="bi bi-geo-alt-fill text-orchid flex-shrink-0 mt-1"></i>
                                    <span>Old Manali Basecamp, Clubhouse Road, Manali, Himachal Pradesh 175131, India</span>
                                </li>
                                <li class="d-flex align-items-center gap-2">
                                    <i class="bi bi-telephone-fill text-orchid flex-shrink-0"></i>
                                    <span>+91 98765 00000 / +91 1902 250000</span>
                                </li>
                                <li class="d-flex align-items-center gap-2">
                                    <i class="bi bi-envelope-fill text-orchid flex-shrink-0"></i>
                                    <span>expeditions@boundlesstreks.com</span>
                                </li>
                                <li class="d-flex align-items-center gap-2">
                                    <i class="bi bi-broadcast text-peach flex-shrink-0"></i>
                                    <span>VHF Emergency Band: 144.200 MHz</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Bottom Copyright Strip -->
                <div class="footer-bottom-strip py-3 border-top border-white-10">
                    <div class="container d-flex flex-column flex-md-row justify-content-between align-items-center gap-2 small text-white-50">
                        <div>
                            &copy; 2026 <strong class="text-white">BoundlessTreks Expeditions Pvt. Ltd.</strong> All rights reserved.
                        </div>
                        <div class="d-flex flex-wrap gap-3">
                            <span class="text-white-50">IMF Accredited</span>
                            <span>&bull;</span>
                            <span class="text-white-50">UIAA Certified</span>
                            <span>&bull;</span>
                            <span class="text-white-50">Leave No Trace Partner</span>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
        `
    });

    if (window.router) {
        app.use(window.router);
    }

    app.mount('#app');
    console.log("BoundlessTreks Vue 3 Single Page Application mounted successfully.");
});

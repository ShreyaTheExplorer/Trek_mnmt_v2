/**
 * Vue Router Configuration for TMA
 * CDN-based Vue Router with Role-Based Access Control (RBAC) route guards.
 */

const { createRouter, createWebHashHistory } = VueRouter;

const routes = [
    {
        path: '/',
        name: 'Home',
        redirect: () => {
            const auth = window.tmaApi.auth;
            if (auth.isAuthenticated()) {
                if (auth.role === 'admin') return '/admin/dashboard';
                if (auth.role === 'staff') return '/staff';
                return '/dashboard';
            }
            return '/login';
        }
    },
    {
        path: '/login',
        name: 'Login',
        component: window.LoginPage,
        meta: { guestOnly: true }
    },
    {
        path: '/register',
        name: 'Register',
        component: window.RegisterPage,
        meta: { guestOnly: true }
    },
    {
        path: '/dashboard',
        name: 'UserDashboard',
        component: window.UserDashboard,
        meta: { requiresAuth: true, roles: ['user'] }
    },
    {
        path: '/user/dashboard',
        redirect: '/dashboard'
    },
    {
        path: '/treks',
        name: 'TrekBrowse',
        component: window.TrekBrowse || window.TrekkerCatalog
    },
    {
        path: '/treks/:id',
        name: 'TrekDetail',
        component: window.TrekDetail
    },
    {
        path: '/my-bookings',
        name: 'MyBookings',
        component: window.MyBookings,
        meta: { requiresAuth: true, roles: ['user'] }
    },
    {
        path: '/staff',
        name: 'StaffDashboard',
        component: window.StaffDashboard || window.StaffDashboardPlaceholder,
        meta: { requiresAuth: true, roles: ['staff'] }
    },
    {
        path: '/staff/treks/:id',
        name: 'StaffTrekDetail',
        component: window.StaffTrekDetail,
        meta: { requiresAuth: true, roles: ['staff'] }
    },
    {
        path: '/admin',
        redirect: '/admin/dashboard'
    },
    {
        path: '/admin/:tab?',
        name: 'AdminPanel',
        component: window.AdminView,
        meta: { requiresAuth: true, roles: ['admin'] }
    },
    {
        path: '/profile',
        name: 'Profile',
        component: window.ProfileView || window.ProfilePlaceholder,
        meta: { requiresAuth: true }
    },
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    }
];

const router = createRouter({
    history: createWebHashHistory(),
    routes
});

// Role-Based Navigation Guards
router.beforeEach((to, from, next) => {
    const auth = window.tmaApi.auth;
    const isLoggedIn = auth.isAuthenticated();
    const userRole = auth.role;

    // 1. Guest-only routes (/login, /register)
    if (to.meta.guestOnly && isLoggedIn) {
        if (userRole === 'admin') return next('/admin/dashboard');
        if (userRole === 'staff') return next('/staff');
        return next('/treks');
    }

    // 2. Protected routes requiring authentication
    if (to.meta.requiresAuth && !isLoggedIn) {
        window.showToast("Please sign in to access this page.", "warning");
        return next('/login');
    }

    // 3. Role-specific protection
    if (to.meta.roles && to.meta.roles.length > 0) {
        if (!to.meta.roles.includes(userRole)) {
            window.showToast("Access forbidden: you do not have permission for this section.", "danger");
            // Redirect to appropriate home for the role
            if (userRole === 'admin') return next('/admin/dashboard');
            if (userRole === 'staff') return next('/staff');
            return next('/treks');
        }
    }

    next();
});

window.router = router;


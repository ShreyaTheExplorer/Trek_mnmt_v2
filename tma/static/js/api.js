/**
 * TMA Frontend API Client
 * Centralized fetch wrapper handling JWT authentication, standard error parsing, and session state.
 */

const API_BASE = '/api';

const authState = {
    token: localStorage.getItem('tma_token') || null,
    role: localStorage.getItem('tma_role') || null,
    user: JSON.parse(localStorage.getItem('tma_user') || 'null'),
    listeners: [],

    subscribe(listener) {
        this.listeners.push(listener);
    },

    notify() {
        this.listeners.forEach(cb => {
            try { cb(this); } catch (e) { console.error(e); }
        });
        try {
            window.dispatchEvent(new CustomEvent('tma-auth-changed', {
                detail: { token: this.token, role: this.role, user: this.user }
            }));
        } catch (e) {}
    },

    setAuth(token, role, user) {
        this.token = token;
        this.role = role;
        this.user = user;
        localStorage.setItem('tma_token', token);
        localStorage.setItem('tma_role', role);
        localStorage.setItem('tma_user', JSON.stringify(user));
        this.notify();
    },

    clearAuth() {
        this.token = null;
        this.role = null;
        this.user = null;
        localStorage.removeItem('tma_token');
        localStorage.removeItem('tma_role');
        localStorage.removeItem('tma_user');
        this.notify();
    },

    isAuthenticated() {
        return !!this.token;
    }
};

const reactiveAuthState = (window.Vue && typeof window.Vue.reactive === 'function')
    ? window.Vue.reactive(authState)
    : authState;

const api = {
    auth: reactiveAuthState,

    async request(path, options = {}) {
        const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
        const headers = options.headers || {};

        if (authState.token) {
            headers['Authorization'] = `Bearer ${authState.token}`;
        }

        if (options.body && !(options.body instanceof FormData) && typeof options.body === 'object') {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }

        options.headers = headers;

        try {
            const response = await fetch(url, options);

            // Handle unauthenticated session
            if (response.status === 401) {
                authState.clearAuth();
                if (window.router) {
                    window.router.push('/login');
                }
                throw new Error("Session expired. Please log in again.");
            }

            // If response is a downloadable blob / file
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('text/csv') || contentType.includes('application/octet-stream')) {
                return await response.blob();
            }

            const json = await response.json();

            if (!response.ok || json.success === false) {
                const errorMsg = json.message || `Request failed with status ${response.status}`;
                const err = new Error(errorMsg);
                err.status = response.status;
                err.data = json.data;
                throw err;
            }

            return json;
        } catch (err) {
            console.error(`[API Error] ${options.method || 'GET'} ${url}:`, err);
            throw err;
        }
    },

    get(path, queryParams = null) {
        let url = path;
        if (queryParams && typeof queryParams === 'object') {
            const query = new URLSearchParams();
            for (const [key, val] of Object.entries(queryParams)) {
                if (val !== undefined && val !== null && val !== '') {
                    query.append(key, val);
                }
            }
            const qs = query.toString();
            if (qs) url += (url.includes('?') ? '&' : '?') + qs;
        }
        return this.request(url, { method: 'GET' });
    },

    post(path, body = {}) {
        return this.request(path, { method: 'POST', body });
    },

    put(path, body = {}) {
        return this.request(path, { method: 'PUT', body });
    },

    patch(path, body = {}) {
        return this.request(path, { method: 'PATCH', body });
    },

    delete(path, body = null) {
        return this.request(path, { method: 'DELETE', body });
    }
};

window.tmaApi = api;


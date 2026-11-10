/**
 * Toast Component
 * Global reactive notification alerts container.
 */

const rawToastState = {
    toasts: [],
    add(message, type = 'success', duration = 4500) {
        const id = Date.now() + Math.random();
        this.toasts.push({ id, message, type });
        if (duration > 0) {
            setTimeout(() => {
                this.remove(id);
            }, duration);
        }
    },
    remove(id) {
        const index = this.toasts.findIndex(t => t.id === id);
        if (index !== -1) {
            this.toasts.splice(index, 1);
        }
    }
};

// Make reactive via Vue 3 if Vue is present
const ToastState = (window.Vue && typeof window.Vue.reactive === 'function')
    ? window.Vue.reactive(rawToastState)
    : rawToastState;

window.ToastState = ToastState;

window.showToast = (msg, type = 'success', duration = 4500) => {
    if (window.ToastState && typeof window.ToastState.add === 'function') {
        window.ToastState.add(msg, type, duration);
    } else {
        console.log(`[Toast ${type}]: ${msg}`);
    }
};

const ToastComponent = {
    name: 'ToastComponent',
    data() {
        return {
            state: window.ToastState || ToastState
        };
    },
    methods: {
        removeToast(id) {
            this.state.remove(id);
        },
        iconForType(type) {
            switch (type) {
                case 'success': return 'bi-check-circle-fill text-success';
                case 'danger': return 'bi-exclamation-triangle-fill text-danger';
                case 'warning': return 'bi-exclamation-circle-fill text-warning';
                default: return 'bi-info-circle-fill text-info';
            }
        }
    },
    template: `
    <div class="tma-toast-container">
        <div v-for="t in state.toasts" :key="t.id" 
             class="toast show align-items-center border-0 shadow-lg mb-2" 
             :class="'bg-white border-start border-4 border-' + (t.type === 'danger' ? 'danger' : t.type)"
             role="alert">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i class="bi fs-5 flex-shrink-0" :class="iconForType(t.type)"></i>
                    <div class="text-dark small fw-medium">{{ t.message }}</div>
                </div>
                <button type="button" class="btn-close me-2 m-auto" @click="removeToast(t.id)"></button>
            </div>
        </div>
    </div>
    `
};

window.ToastComponent = ToastComponent;

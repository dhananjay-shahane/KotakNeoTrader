// Dashboard JavaScript functionality for Kotak Neo Trading App

class TradingDashboard {
    constructor() {
        this.isConnected = false;
        this.refreshInterval = null;
        this.wsHandler = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
        this.initializeWebSocket();
        console.log('Trading Dashboard initialized');
    }

    setupEventListeners() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.initializeEventListeners();
            });
        } else {
            this.initializeEventListeners();
        }
    }

    initializeEventListeners() {
        // Safely add event listeners only if elements exist
        try {
            // Refresh button click handlers
            const refreshButtons = document.querySelectorAll('[onclick*="refresh"]');
            refreshButtons.forEach(btn => {
                if (btn && typeof btn.addEventListener === 'function') {
                    btn.addEventListener('click', this.handleRefresh.bind(this));
                }
            });

            // Order form submissions
            const orderForms = document.querySelectorAll('form[id*="Order"]');
            orderForms.forEach(form => {
                if (form && typeof form.addEventListener === 'function') {
                    form.addEventListener('submit', this.handleOrderSubmit.bind(this));
                }
            });

            // Real-time price updates
            this.setupPriceUpdateHandlers();
        } catch (error) {
            console.warn('Error initializing event listeners:', error);
        }
    }

    setupPriceUpdateHandlers() {
        // Find all price elements and mark them for real-time updates
        const priceElements = document.querySelectorAll('[data-price], .price-ltp, [id*="ltp"]');
        priceElements.forEach(element => {
            element.classList.add('live-data');
        });
    }

    handleRefresh(event) {
        const button = event.target.closest('button');
        if (button) {
            button.classList.add('loading');
            setTimeout(() => {
                button.classList.remove('loading');
            }, 1000);
        }
    }

    handleOrderSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');

        if (submitBtn) {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
        }

        // Form submission will be handled by individual page scripts
        setTimeout(() => {
            if (submitBtn) {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }
        }, 2000);
    }

    startAutoRefresh() {
        // Auto-refresh critical data every 10 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshCriticalData();
        }, 10000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    async refreshCriticalData() {
        try {
            // Refresh specific sections without full page reload
            await this.refreshDashboardSection('quotes');
            await this.refreshDashboardSection('positions');
            await this.refreshDashboardSection('orders');
            await this.updatePortfolioSummary();

            // Only log if debug mode is enabled
            if (window.location.search.includes('debug=true')) {
                console.log('Critical data refreshed');
            }
        } catch (error) {
            console.error('Error refreshing critical data:', error);
        }
    }

    async refreshDashboardSection(section) {
        try {
            let endpoint = '';
            let targetElement = '';

            switch(section) {
                case 'quotes':
                    endpoint = '/api/dashboard_quotes';
                    targetElement = '#quotesTableBody';
                    break;
                case 'positions':
                    endpoint = '/api/dashboard_positions';
                    targetElement = '#positionsTableBody';
                    break;
                case 'orders':
                    endpoint = '/api/dashboard_orders';
                    targetElement = '#ordersTableBody';
                    break;
                default:
                    return;
            }

            const response = await fetch(endpoint);
            const data = await response.json();

            if (data.success && data.html) {
                const element = document.querySelector(targetElement);
                if (element) {
                    element.innerHTML = data.html;
                    console.log(`${section} section refreshed`);
                }
            }
        } catch (error) {
            console.warn(`Error refreshing ${section} section:`, error);
        }
    }

    async updatePositionsPnL() {
        // This would fetch latest P&L for positions
        // Implementation depends on your WebSocket or API structure
        const positions = document.querySelectorAll('[data-position-pnl]');
        positions.forEach(element => {
            // Simulate price update animation
            this.animatePriceChange(element);
        });
    }

    async updateHoldingsValues() {
        // This would fetch latest values for holdings
        const holdings = document.querySelectorAll('[data-holding-value]');
        holdings.forEach(element => {
            this.animatePriceChange(element);
        });
    }

    async updatePortfolioSummary() {
        // Update summary statistics
        const summaryElements = document.querySelectorAll('[data-portfolio-summary]');
        summaryElements.forEach(element => {
            element.classList.add('live-data');
        });
    }

    animatePriceChange(element, newValue = null, oldValue = null) {
        if (!element) return;

        // Remove existing animation classes
        element.classList.remove('price-up', 'price-down');

        if (newValue !== null && oldValue !== null) {
            if (newValue > oldValue) {
                element.classList.add('price-up');
            } else if (newValue < oldValue) {
                element.classList.add('price-down');
            }
        } else {
            // Random animation for demo (remove in production)
            const isUp = Math.random() > 0.5;
            element.classList.add(isUp ? 'price-up' : 'price-down');
        }

        // Remove animation class after animation completes
        setTimeout(() => {
            element.classList.remove('price-up', 'price-down');
        }, 500);
    }

    initializeWebSocket() {
        // Initialize WebSocket connection for real-time data
        // This will be handled by websocket.js
        if (window.WebSocketHandler) {
            this.wsHandler = new window.WebSocketHandler();
            this.wsHandler.connect();
        }
    }

    // Utility methods for order management
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    formatPercentage(value) {
        return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Order management helpers
    async placeOrder(orderData) {
        try {
            const response = await fetch('/api/place_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Order placed successfully!', 'success');
                return result.data;
            } else {
                this.showNotification(`Failed to place order: ${result.message}`, 'danger');
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Error placing order:', error);
            this.showNotification('Error placing order', 'danger');
            throw error;
        }
    }

    async modifyOrder(orderData) {
        try {
            const response = await fetch('/api/modify_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Order modified successfully!', 'success');
                return result.data;
            } else {
                this.showNotification(`Failed to modify order: ${result.message}`, 'danger');
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Error modifying order:', error);
            this.showNotification('Error modifying order', 'danger');
            throw error;
        }
    }

    async cancelOrder(orderId) {
        try {
            const response = await fetch('/api/cancel_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ order_id: orderId, isVerify: true })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Order cancelled successfully!', 'success');
                return result.data;
            } else {
                this.showNotification(`Failed to cancel order: ${result.message}`, 'danger');
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Error cancelling order:', error);
            this.showNotification('Error cancelling order', 'danger');
            throw error;
        }
    }

    // Cleanup method
    destroy() {
        this.stopAutoRefresh();
        if (this.wsHandler) {
            this.wsHandler.disconnect();
        }
        console.log('Trading Dashboard destroyed');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on an authenticated page
    if (document.querySelector('.navbar')) {
        window.tradingDashboard = new TradingDashboard();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.tradingDashboard) {
        window.tradingDashboard.destroy();
    }
});

// Global utility functions
window.TradingUtils = {
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    },

    formatPercentage: function(value) {
        return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
    },

    formatNumber: function(value, decimals = 2) {
        return parseFloat(value).toFixed(decimals);
    },

    getPnLClass: function(value) {
        if (value > 0) return 'text-success';
        if (value < 0) return 'text-danger';
        return 'text-muted';
    },

    animateValue: function(element, start, end, duration = 1000) {
        const range = end - start;
        const minTimer = 50;
        let stepTime = Math.abs(Math.floor(duration / range));
        stepTime = Math.max(stepTime, minTimer);

        const startTime = new Date().getTime();
        const endTime = startTime + duration;

        function run() {
            const now = new Date().getTime();
            const remaining = Math.max((endTime - now) / duration, 0);
            const value = Math.round(end - (remaining * range));
            element.textContent = value;

            if (value === end) {
                return;
            }

            setTimeout(run, stepTime);
        }

        run();
    }
};

// Dashboard-specific JavaScript functions
function openPlaceOrderModal(type) {
    const transactionSelect = document.querySelector('select[name="transaction_type"]');
    if (transactionSelect) {
        transactionSelect.value = type;
    }
    const modal = document.getElementById('placeOrderModal');
    if (modal) {
        new bootstrap.Modal(modal).show();
    }
}
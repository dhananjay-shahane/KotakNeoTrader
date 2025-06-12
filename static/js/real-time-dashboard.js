// Real-time Dashboard Updates - No Page Refresh System
class RealTimeDashboard {
    constructor() {
        this.refreshInterval = null;
        this.isRefreshing = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
        this.addCustomCSS();
        console.log('Real-time dashboard initialized');
    }

    addCustomCSS() {
        const style = document.createElement('style');
        style.textContent = `
            .data-updated {
                animation: dataUpdate 1.5s ease-in-out;
            }
            
            @keyframes dataUpdate {
                0% { background-color: rgba(40, 167, 69, 0.3); }
                50% { background-color: rgba(40, 167, 69, 0.1); }
                100% { background-color: transparent; }
            }
            
            .refresh-loading {
                opacity: 0.7;
                pointer-events: none;
            }
            
            .refresh-loading::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #007bff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: translate(-50%, -50%) rotate(0deg); }
                100% { transform: translate(-50%, -50%) rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }

    setupEventListeners() {
        // Override refresh button clicks to use AJAX
        document.addEventListener('click', (e) => {
            if (e.target.closest('[onclick*="refreshDashboard"]')) {
                e.preventDefault();
                e.stopPropagation();
                this.manualRefresh();
            }
        });

        // Prevent default refresh behaviors
        const refreshButtons = document.querySelectorAll('[onclick*="refresh"]');
        refreshButtons.forEach(btn => {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.manualRefresh();
            });
        });
    }

    startAutoRefresh() {
        // Auto-refresh every 30 seconds for real-time feel
        this.refreshInterval = setInterval(() => {
            if (!this.isRefreshing) {
                this.refreshData();
            }
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    async manualRefresh() {
        const refreshBtn = document.querySelector('[onclick*="refreshDashboard"], .btn:contains("Refresh")');
        if (refreshBtn) {
            refreshBtn.classList.add('refresh-loading');
        }
        
        await this.refreshData();
        
        if (refreshBtn) {
            refreshBtn.classList.remove('refresh-loading');
        }
    }

    async refreshData() {
        if (this.isRefreshing) return;
        
        this.isRefreshing = true;
        
        try {
            const response = await fetch('/api/dashboard_data', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.updateDashboardElements(data);
            this.showSuccessIndicator();

        } catch (error) {
            console.error('Dashboard refresh error:', error);
            this.showErrorNotification(error.message);
        } finally {
            this.isRefreshing = false;
        }
    }

    updateDashboardElements(data) {
        // Update total positions
        this.updateElement('totalPositions', data.total_positions || 0);
        
        // Update total holdings
        this.updateElement('totalHoldings', data.total_holdings || 0);
        
        // Update available margin
        if (data.limits) {
            const margin = data.limits.Net || data.limits.net || data.limits.Collateral || 0;
            this.updateElement('availableMargin', `₹${this.formatCurrency(margin)}`);
            
            const marginUsed = data.limits.MarginUsed || data.limits.marginUsed || data.limits.MarginUsedPrsnt || 0;
            const marginUsedEl = document.getElementById('marginUsed');
            if (marginUsedEl) {
                marginUsedEl.innerHTML = `<i class="fas fa-rupee-sign me-1"></i>Used: ₹${this.formatCurrency(marginUsed)}`;
                this.addUpdateAnimation(marginUsedEl);
            }
        }

        // Update holdings value
        if (data.holdings && Array.isArray(data.holdings)) {
            const totalValue = data.holdings.reduce((sum, holding) => {
                // Handle different API response formats for holdings
                const value = parseFloat(
                    holding.LastPrice || 
                    holding.ltp || 
                    holding.marketPrice || 
                    holding.mktPrice || 
                    holding.marketValue || 
                    0
                );
                const qty = parseFloat(
                    holding.Quantity || 
                    holding.quantity || 
                    holding.holdingQty || 
                    holding.NetQuantity || 
                    0
                );
                return sum + (value * qty);
            }, 0);
            
            const holdingsValueEl = document.getElementById('holdingsValue');
            if (holdingsValueEl) {
                holdingsValueEl.innerHTML = `<i class="fas fa-wallet me-1"></i>₹${this.formatCurrency(totalValue)}`;
                this.addUpdateAnimation(holdingsValueEl);
            }
        }

        // Update last refresh time
        this.updateLastRefreshTime();
        
        console.log('Dashboard updated successfully');
    }

    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            this.addUpdateAnimation(element);
        }
    }

    addUpdateAnimation(element) {
        element.classList.remove('data-updated');
        // Force reflow
        element.offsetHeight;
        element.classList.add('data-updated');
    }

    formatCurrency(amount) {
        const number = parseFloat(amount) || 0;
        return number.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    updateLastRefreshTime() {
        const lastLoginEl = document.getElementById('lastLoginTime');
        if (lastLoginEl) {
            const now = new Date();
            lastLoginEl.textContent = now.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }

    showSuccessIndicator() {
        // Brief success indicator
        const indicator = document.createElement('div');
        indicator.className = 'position-fixed bg-success text-white px-3 py-2 rounded';
        indicator.style.cssText = 'top: 20px; right: 20px; z-index: 9999; font-size: 0.9rem;';
        indicator.innerHTML = '<i class="fas fa-check me-1"></i>Updated';
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.style.opacity = '0';
            indicator.style.transition = 'opacity 0.3s ease';
            setTimeout(() => indicator.remove(), 300);
        }, 2000);
    }

    showErrorNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-warning position-fixed shadow-lg';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 350px; max-width: 400px;';
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div class="flex-grow-1">
                    <strong>Refresh Failed</strong><br>
                    <small>${message}</small>
                </div>
                <button type="button" class="btn-close" onclick="this.closest('.alert').remove()"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.opacity = '0';
                notification.style.transition = 'opacity 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 8000);
    }

    destroy() {
        this.stopAutoRefresh();
        console.log('Real-time dashboard destroyed');
    }
}

// Global function for backward compatibility
function refreshDashboard() {
    if (window.realTimeDashboard) {
        window.realTimeDashboard.manualRefresh();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.realTimeDashboard = new RealTimeDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.realTimeDashboard) {
        window.realTimeDashboard.destroy();
    }
});
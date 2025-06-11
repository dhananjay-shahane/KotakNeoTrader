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
        // Auto-refresh critical data every 5 minutes to reduce API calls
        this.refreshInterval = setInterval(() => {
            this.refreshCriticalData();
        }, 300000); // 5 minutes instead of 10 seconds
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
            await this.refreshPortfolioSummary();

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

    async refreshPortfolioSummary() {
        try {
            console.log('Refreshing portfolio summary...');
            const response = await fetch('/api/portfolio_summary');
            const data = await response.json();

            if (data.success) {
                this.updatePortfolioCards(data);
                // Only show notification in debug mode
                if (window.location.search.includes('debug=true')) {
                    this.showNotification('Portfolio updated successfully', 'success');
                }
            } else {
                console.error('Failed to refresh portfolio:', data.message);
                this.showNotification('Failed to update portfolio', 'error');
            }
        } catch (error) {
            console.error('Error refreshing portfolio:', error);
            this.showNotification('Error updating portfolio', 'error');
        }
    }

    updatePortfolioCards(data) {
        // Update total positions
        const totalPositionsEl = document.getElementById('totalPositions');
        if (totalPositionsEl && data.total_positions !== undefined) {
            totalPositionsEl.textContent = data.total_positions;
        }

        // Update total holdings
        const totalHoldingsEl = document.getElementById('totalHoldings');
        if (totalHoldingsEl && data.total_holdings !== undefined) {
            totalHoldingsEl.textContent = data.total_holdings;
        }

        // Update total orders (if available)
        const totalOrdersEl = document.getElementById('totalOrders');
        if (totalOrdersEl && data.total_orders !== undefined) {
            totalOrdersEl.textContent = data.total_orders;
        }

        // Update available margin
        const availableMarginEl = document.getElementById('availableMargin');
        if (availableMarginEl && data.limits_available !== undefined) {
            const margin = parseFloat(data.limits_available) || 0;
            availableMarginEl.textContent = `₹${margin.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        }

        // Update P&L in account summary modal if visible
        const portfolioPnlEl = document.querySelector('.portfolio-pnl');
        if (portfolioPnlEl && data.total_pnl !== undefined) {
            const pnl = parseFloat(data.total_pnl) || 0;
            portfolioPnlEl.textContent = `₹${pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
            portfolioPnlEl.className = `portfolio-pnl ${pnl >= 0 ? 'text-success' : 'text-danger'}`;
        }

        // Update investment value in account summary modal if visible
        const portfolioInvestmentEl = document.querySelector('.portfolio-investment');
        if (portfolioInvestmentEl && data.total_investment !== undefined) {
            const investment = parseFloat(data.total_investment) || 0;
            portfolioInvestmentEl.textContent = `₹${investment.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        }

        // Update portfolio last update timestamp
        const portfolioLastUpdateEl = document.getElementById('portfolioLastUpdate');
        if (portfolioLastUpdateEl) {
            const now = new Date();
            portfolioLastUpdateEl.textContent = now.toLocaleTimeString();
        }
    }

    async refreshPortfolioDetails() {
        try {
            console.log('Refreshing detailed portfolio data...');
            const response = await fetch('/api/portfolio_details');
            const data = await response.json();

            if (data.success) {
                // Update portfolio section with detailed data
                this.updatePortfolioSection(data.data);
                this.displayRawPortfolioData(data.data);
                this.showNotification('Portfolio details updated', 'success');
            } else {
                console.error('Failed to refresh portfolio details:', data.message);
                this.showNotification('Failed to update portfolio details', 'error');
            }
        } catch (error) {
            console.error('Error refreshing portfolio details:', error);
            this.showNotification('Error updating portfolio details', 'error');
        }
    }

    displayRawPortfolioData(portfolioData) {
        const displayElement = document.getElementById('portfolioDataDisplay');
        if (!displayElement) return;

        let html = '<div class="row">';

        // Display Positions Data
        if (portfolioData.positions) {
            html += `
                <div class="col-md-6 mb-3">
                    <h6 class="text-info">Positions Data</h6>
                    <div class="bg-dark p-3 rounded">
                        <pre class="text-light mb-0" style="font-size: 0.8rem; max-height: 300px; overflow-y: auto;">${JSON.stringify(portfolioData.positions, null, 2)}</pre>
                    </div>
                </div>
            `;
        }

        // Display Holdings Data
        if (portfolioData.holdings) {
            html += `
                <div class="col-md-6 mb-3">
                    <h6 class="text-info">Holdings Data</h6>
                    <div class="bg-dark p-3 rounded">
                        <pre class="text-light mb-0" style="font-size: 0.8rem; max-height: 300px; overflow-y: auto;">${JSON.stringify(portfolioData.holdings, null, 2)}</pre>
                    </div>
                </div>
            `;
        }

        // Display Limits Data
        if (portfolioData.limits) {
            html += `
                <div class="col-12 mb-3">
                    <h6 class="text-info">Limits Data</h6>
                    <div class="bg-dark p-3 rounded">
                        <pre class="text-light mb-0" style="font-size: 0.8rem; max-height: 200px; overflow-y: auto;">${JSON.stringify(portfolioData.limits, null, 2)}</pre>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        displayElement.innerHTML = html;

        // Update detailed tables
        this.updatePositionsTable(portfolioData.positions?.data || []);
        this.updateHoldingsTable(portfolioData.holdings?.data || []);
        this.updateLimitsDisplay(portfolioData.limits);
    }

    updateHoldingsTable(holdings) {
        const tableBody = document.getElementById('holdingsTableBody');
        if (!tableBody) return;

        if (holdings.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No holdings found</td></tr>';
            return;
        }

        tableBody.innerHTML = '';

        holdings.forEach(holding => {
            const row = document.createElement('tr');
            const quantity = parseFloat(holding.quantity || 0);
            const avgPrice = parseFloat(holding.avgPrice || 0);
            const ltp = parseFloat(holding.ltp || 0);
            const marketValue = quantity * ltp;
            const investedValue = quantity * avgPrice;
            const pnl = marketValue - investedValue;

            row.innerHTML = `
                <td>
                    <strong>${holding.trdSym || holding.sym || 'N/A'}</strong>
                    <br><small class="text-muted">${holding.series || ''}</small>
                </td>
                <td><span class="badge bg-info">${holding.exSeg || 'N/A'}</span></td>
                <td class="text-center">${quantity}</td>
                <td class="text-end">₹${avgPrice.toFixed(2)}</td>
                <td class="text-end">₹${ltp.toFixed(2)}</td>
                <td class="text-end">₹${marketValue.toFixed(2)}</td>
                <td class="text-end ${pnl >= 0 ? 'text-success' : 'text-danger'}">
                    ₹${pnl.toFixed(2)}
                </td>
                <td class="text-center">
                    <span class="badge ${holding.sqrFlg === 'Y' ? 'bg-success' : 'bg-warning'}">
                        ${holding.sqrFlg === 'Y' ? 'Active' : 'Inactive'}
                    </span>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    updateLimitsDisplay(limits) {
        const displayElement = document.getElementById('limitsDisplay');
        if (!displayElement) return;

        if (!limits || !limits.data) {
            displayElement.innerHTML = '<p class="text-muted">No limits data available</p>';
            return;
        }

        const limitsData = limits.data;
        let html = '<div class="row">';

        // Display key limit fields
        const keyFields = ['cash', 'payin', 'payout', 'buyingPower', 'utilizedMargin', 'availableMargin'];

        keyFields.forEach(field => {
            if (limitsData[field] !== undefined) {
                html += `
                    <div class="col-md-4 mb-2">
                        <strong>${field}:</strong> 
                        <span class="text-success">₹${parseFloat(limitsData[field] || 0).toFixed(2)}</span>
                    </div>
                `;
            }
        });

        html += '</div>';
        displayElement.innerHTML = html;
    }

    updatePortfolioSection(portfolioData) {
        // Update P&L display
        const totalPnlElement = document.querySelector('.portfolio-pnl');
        if (totalPnlElement && portfolioData.summary) {
            const pnl = portfolioData.summary.total_pnl;
            totalPnlElement.textContent = `₹${pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
            totalPnlElement.className = `portfolio-pnl ${pnl >= 0 ? 'text-success' : 'text-danger'}`;
        }

        // Update investment value
        const investmentElement = document.querySelector('.portfolio-investment');
        if (investmentElement && portfolioData.summary) {
            const investment = portfolioData.summary.total_investment;
            investmentElement.textContent = `₹${investment.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        }

        // Update positions table if visible
        if (portfolioData.positions && portfolioData.positions.data) {
            this.updatePositionsTable(portfolioData.positions.data);
        }
    }

    updatePositionsTable(positions) {
        const tableBody = document.getElementById('positionsTableBody');
        if (!tableBody) return;

        if (positions.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No positions found</td></tr>';
            return;
        }

        tableBody.innerHTML = '';

        positions.forEach(position => {
            const row = document.createElement('tr');
            const buyQty = parseFloat(position.flBuyQty || 0);
            const sellQty = parseFloat(position.flSellQty || 0);
            const netQty = buyQty - sellQty;
            const buyAmt = parseFloat(position.buyAmt || 0);
            const sellAmt = parseFloat(position.sellAmt || 0);
            const pnl = sellAmt - buyAmt;

            row.innerHTML = `
                <td>
                    <strong>${position.trdSym || position.sym || 'N/A'}</strong>
                    <br><small class="text-muted">${position.series || ''}</small>
                </td>
                <td><span class="badge bg-info">${position.exSeg || 'N/A'}</span></td>
                <td><span class="badge bg-secondary">${position.prod || 'N/A'}</span></td>
                <td class="text-center text-success">${buyQty}</td>
                <td class="text-center text-danger">${sellQty}</td>
                <td class="text-center">
                    <span class="badge ${netQty > 0 ? 'bg-success' : netQty < 0 ? 'bg-danger' : 'bg-secondary'}">
                        ${netQty}
                    </span>
                </td>
                <td class="text-end">₹${buyAmt.toFixed(2)}</td>
                <td class="text-end">₹${sellAmt.toFixed(2)}</td>
                <td class="text-end ${pnl >= 0 ? 'text-success' : 'text-danger'}">
                    ₹${pnl.toFixed(2)}
                </td>
                <td class="text-center">
                    <span class="badge ${position.sqrFlg === 'Y' ? 'bg-success' : 'bg-warning'}">
                        ${position.sqrFlg === 'Y' ? 'Active' : 'Inactive'}
                    </span>
                </td>
            `;
            tableBody.appendChild(row);
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
    loadLiveQuotes() {
        fetch('/api/live_quotes')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.displayLiveQuotes(data.quotes);
                } else {
                    console.error('Failed to load live quotes:', data.message);
                    document.getElementById('live-quotes').innerHTML = 
                        '<div class="text-danger"><i class="fas fa-exclamation-triangle"></i> Failed to load quotes</div>';
                }
            })
            .catch(error => {
                console.error('Error loading live quotes:', error);
                document.getElementById('live-quotes').innerHTML = 
                    '<div class="text-danger"><i class="fas fa-exclamation-triangle"></i> Error loading quotes</div>';
            });
    }

    loadUserProfile() {
        fetch('/api/user_profile')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.displayUserProfile(data.profile);
                } else {
                    console.error('Failed to load user profile:', data.message);
                    document.getElementById('user-profile').innerHTML = 
                        '<div class="text-danger"><i class="fas fa-exclamation-triangle"></i> Failed to load profile</div>';
                }
            })
            .catch(error => {
                console.error('Error loading user profile:', error);
                document.getElementById('user-profile').innerHTML = 
                    '<div class="text-danger"><i class="fas fa-exclamation-triangle"></i> Error loading profile</div>';
            });
    }
    displayLiveQuotes(quotes) {
        const quotesContainer = document.getElementById('live-quotes');
        if (!quotes || quotes.length === 0) {
            quotesContainer.innerHTML = '<div class="text-muted">No live quotes available</div>';
            return;
        }

        const quotesHtml = quotes.map(quote => `
            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                <div>
                    <strong>${quote.symbol}</strong>
                </div>
                <div class="text-end">
                    <div class="fw-bold ${quote.changePct >= 0 ? 'text-success' : 'text-danger'}">
                        ₹${quote.ltp}
                    </div>
                    <small class="${quote.changePct >= 0 ? 'text-success' : 'text-danger'}">
                        ${quote.changePct >= 0 ? '+' : ''}${quote.changePct}%
                    </small>
                </div>
            </div>
        `).join('');

        quotesContainer.innerHTML = quotesHtml;
    }

    displayUserProfile(profile) {
        const profileContainer = document.getElementById('user-profile');

        const statusColor = profile.token_status === 'Valid' ? 'success' : 'danger';
        const statusIcon = profile.token_status === 'Valid' ? 'check-circle' : 'exclamation-triangle';

        const profileHtml = `
            <div class="row g-2">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="mb-0">
                            <i class="fas fa-user me-2"></i>${profile.greeting_name}
                        </h6>
                        <span class="badge bg-${statusColor}">
                            <i class="fas fa-${statusIcon} me-1"></i>${profile.token_status}
                        </span>
                    </div>
                </div>
                <div class="col-6">
                    <small class="text-muted">UCC</small>
                    <div class="fw-bold">${profile.ucc}</div>
                </div>
                <div class="col-6">
                    <small class="text-muted">Login Time</small>
                    <div class="fw-bold">${profile.login_time}</div>
                </div>
                <div class="col-12 mt-2">
                    <small class="text-muted">Session Token</small>
                    <div class="text-truncate small" style="font-family: monospace;">${profile.session_token}</div>
                </div>
                ${profile.needs_reauth ? `
                <div class="col-12 mt-2">
                    <div class="alert alert-warning alert-sm mb-0 py-2">
                        <i class="fas fa-exclamation-triangle me-1"></i>
                        <small>Session expired. Please <a href="/logout">re-login</a>.</small>
                    </div>
                </div>
                ` : ''}
            </div>
        `;

        profileContainer.innerHTML = profileHtml;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on an authenticated page
    if (document.querySelector('.navbar')) {
        window.tradingDashboard = new TradingDashboard();
        // Load live quotes
        window.tradingDashboard.loadLiveQuotes();

        // Load user profile
        window.tradingDashboard.loadUserProfile();
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
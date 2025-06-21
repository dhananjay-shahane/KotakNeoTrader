// ETF Signals Deals Management - ES5 Compatible
function ETFSignalsManager() {
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.rowsPerPage = 50;
    this.refreshInterval = null;
    this.refreshIntervalMs = 30000; // 30 seconds
    this.isRefreshing = false;
    this.visibleColumns = {
        'symbol': true,
        'signal_type': true,
        'entry_price': true,
        'current_price': true,
        'target_price': true,
        'stop_loss': true,
        'quantity': true,
        'investment_amount': true,
        'current_value': true,
        'pnl': true,
        'pnl_percentage': true,
        'status': true,
        'created_at': true,
        'actions': true
    };
    this.filters = {
        signalType: '',
        status: '',
        symbol: '',
        minPnl: '',
        maxPnl: ''
    };
    this.init();
}

ETFSignalsManager.prototype.init = function() {
    this.setupEventListeners();
    this.initializeTable();
    this.loadSignals();
    this.startAutoRefresh();
    console.log('ETF Signals Manager initialized');
};

ETFSignalsManager.prototype.setupEventListeners = function() {
    var self = this;
    
    // Auto refresh toggle
    var autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function(e) {
            if (e.target.checked) {
                self.startAutoRefresh();
            } else {
                self.stopAutoRefresh();
            }
        });
    }
    
    // Filter inputs
    var signalTypeFilter = document.getElementById('signalTypeFilter');
    if (signalTypeFilter) {
        signalTypeFilter.addEventListener('change', function(e) {
            self.filters.signalType = e.target.value;
        });
    }
    
    var statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function(e) {
            self.filters.status = e.target.value;
        });
    }
    
    var symbolFilter = document.getElementById('symbolFilter');
    if (symbolFilter) {
        symbolFilter.addEventListener('input', function(e) {
            self.filters.symbol = e.target.value;
        });
    }
    
    var minPnlFilter = document.getElementById('minPnlFilter');
    if (minPnlFilter) {
        minPnlFilter.addEventListener('input', function(e) {
            self.filters.minPnl = e.target.value;
        });
    }
    
    var maxPnlFilter = document.getElementById('maxPnlFilter');
    if (maxPnlFilter) {
        maxPnlFilter.addEventListener('input', function(e) {
            self.filters.maxPnl = e.target.value;
        });
    }
};

ETFSignalsManager.prototype.initializeTable = function() {
    this.updateTableHeaders();
    this.updateColumnCheckboxes();
};

ETFSignalsManager.prototype.updateTableHeaders = function() {
    var headers = document.getElementById('tableHeaders');
    if (!headers) return;
    
    var headerDefinitions = [
        { key: 'symbol', label: 'Symbol', icon: 'fas fa-tag' },
        { key: 'signal_type', label: 'Signal', icon: 'fas fa-arrow-up' },
        { key: 'entry_price', label: 'Entry Price', icon: 'fas fa-rupee-sign' },
        { key: 'current_price', label: 'Current Price', icon: 'fas fa-chart-line' },
        { key: 'target_price', label: 'Target', icon: 'fas fa-bullseye' },
        { key: 'stop_loss', label: 'Stop Loss', icon: 'fas fa-shield-alt' },
        { key: 'quantity', label: 'Qty', icon: 'fas fa-sort-numeric-up' },
        { key: 'investment_amount', label: 'Investment', icon: 'fas fa-coins' },
        { key: 'current_value', label: 'Current Value', icon: 'fas fa-chart-bar' },
        { key: 'pnl', label: 'P&L', icon: 'fas fa-balance-scale' },
        { key: 'pnl_percentage', label: 'P&L %', icon: 'fas fa-percentage' },
        { key: 'status', label: 'Status', icon: 'fas fa-info-circle' },
        { key: 'created_at', label: 'Created', icon: 'fas fa-clock' },
        { key: 'actions', label: 'Actions', icon: 'fas fa-cogs' }
    ];
    
    headers.innerHTML = '';
    for (var i = 0; i < headerDefinitions.length; i++) {
        var header = headerDefinitions[i];
        if (this.visibleColumns[header.key]) {
            var th = document.createElement('th');
            th.innerHTML = '<i class="' + header.icon + ' me-1"></i>' + header.label;
            th.className = 'text-center';
            th.style.whiteSpace = 'nowrap';
            headers.appendChild(th);
        }
    }
};

ETFSignalsManager.prototype.loadSignals = function() {
    var self = this;
    this.isRefreshing = true;
    this.showLoadingState(true);
    
    fetch('/api/etf/signals')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                self.signals = data.signals || [];
                self.applyFilters();
                self.renderTable();
                self.updateCounts();
            } else {
                self.showAlert('Error loading signals: ' + (data.message || 'Unknown error'), 'danger');
            }
        })
        .catch(function(error) {
            console.error('Error loading signals:', error);
            self.showAlert('Failed to load signals', 'danger');
        })
        .finally(function() {
            self.isRefreshing = false;
            self.showLoadingState(false);
        });
};

ETFSignalsManager.prototype.applyFilters = function() {
    var self = this;
    this.filteredSignals = this.signals.filter(function(signal) {
        // Signal type filter
        if (self.filters.signalType && signal.signal_type !== self.filters.signalType) {
            return false;
        }
        
        // Status filter
        if (self.filters.status && signal.status !== self.filters.status) {
            return false;
        }
        
        // Symbol filter
        if (self.filters.symbol && signal.symbol.toLowerCase().indexOf(self.filters.symbol.toLowerCase()) === -1) {
            return false;
        }
        
        // P&L filters
        var pnl = parseFloat(signal.pnl) || 0;
        if (self.filters.minPnl && pnl < parseFloat(self.filters.minPnl)) {
            return false;
        }
        if (self.filters.maxPnl && pnl > parseFloat(self.filters.maxPnl)) {
            return false;
        }
        
        return true;
    });
    
    this.currentPage = 1; // Reset to first page after filtering
};

ETFSignalsManager.prototype.renderTable = function() {
    var tbody = document.getElementById('signalsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    var startIndex = (this.currentPage - 1) * this.rowsPerPage;
    var endIndex = Math.min(startIndex + this.rowsPerPage, this.filteredSignals.length);
    
    for (var i = startIndex; i < endIndex; i++) {
        var signal = this.filteredSignals[i];
        var row = this.createSignalRow(signal);
        tbody.appendChild(row);
    }
    
    this.updatePagination();
};

ETFSignalsManager.prototype.createSignalRow = function(signal) {
    var row = document.createElement('tr');
    row.className = 'signal-row';
    
    var cells = [];
    
    // Symbol
    if (this.visibleColumns.symbol) {
        cells.push('<td class="fw-bold text-info">' + (signal.symbol || '') + '</td>');
    }
    
    // Signal Type
    if (this.visibleColumns.signal_type) {
        var signalClass = signal.signal_type === 'BUY' ? 'text-success' : 'text-danger';
        var signalIcon = signal.signal_type === 'BUY' ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
        cells.push('<td><i class="' + signalIcon + ' me-1 ' + signalClass + '"></i><span class="' + signalClass + '">' + (signal.signal_type || '') + '</span></td>');
    }
    
    // Entry Price
    if (this.visibleColumns.entry_price) {
        cells.push('<td>₹' + (parseFloat(signal.entry_price) || 0).toFixed(2) + '</td>');
    }
    
    // Current Price
    if (this.visibleColumns.current_price) {
        var priceChange = this.calculatePriceChange(signal.entry_price, signal.current_price);
        var priceClass = priceChange >= 0 ? 'text-success' : 'text-danger';
        cells.push('<td class="' + priceClass + '">₹' + (parseFloat(signal.current_price) || 0).toFixed(2) + '</td>');
    }
    
    // Target Price
    if (this.visibleColumns.target_price) {
        cells.push('<td>₹' + (parseFloat(signal.target_price) || 0).toFixed(2) + '</td>');
    }
    
    // Stop Loss
    if (this.visibleColumns.stop_loss) {
        cells.push('<td>₹' + (parseFloat(signal.stop_loss) || 0).toFixed(2) + '</td>');
    }
    
    // Quantity
    if (this.visibleColumns.quantity) {
        cells.push('<td>' + (signal.quantity || 0) + '</td>');
    }
    
    // Investment Amount
    if (this.visibleColumns.investment_amount) {
        cells.push('<td>₹' + (parseFloat(signal.investment_amount) || 0).toFixed(2) + '</td>');
    }
    
    // Current Value
    if (this.visibleColumns.current_value) {
        cells.push('<td>₹' + (parseFloat(signal.current_value) || 0).toFixed(2) + '</td>');
    }
    
    // P&L
    if (this.visibleColumns.pnl) {
        var pnl = parseFloat(signal.pnl) || 0;
        var pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
        var pnlIcon = pnl >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
        cells.push('<td class="' + pnlClass + '"><i class="' + pnlIcon + ' me-1"></i>₹' + pnl.toFixed(2) + '</td>');
    }
    
    // P&L Percentage
    if (this.visibleColumns.pnl_percentage) {
        var pnlPct = parseFloat(signal.pnl_percentage) || 0;
        var pnlPctClass = pnlPct >= 0 ? 'text-success' : 'text-danger';
        cells.push('<td class="' + pnlPctClass + '">' + pnlPct.toFixed(2) + '%</td>');
    }
    
    // Status
    if (this.visibleColumns.status) {
        var statusClass = this.getStatusClass(signal.status);
        cells.push('<td><span class="badge ' + statusClass + '">' + (signal.status || '') + '</span></td>');
    }
    
    // Created At
    if (this.visibleColumns.created_at) {
        var createdAt = signal.created_at ? new Date(signal.created_at).toLocaleDateString() : '';
        cells.push('<td class="text-muted">' + createdAt + '</td>');
    }
    
    // Actions
    if (this.visibleColumns.actions) {
        var actionButtons = 
            '<button class="btn btn-sm btn-outline-primary me-1" onclick="etfSignalsManager.showTradeModal(\'' + signal.id + '\')" title="Execute Signal">' +
            '<i class="fas fa-play"></i>' +
            '</button>' +
            '<button class="btn btn-sm btn-outline-info me-1" onclick="etfSignalsManager.showChart(\'' + signal.symbol + '\')" title="View Chart">' +
            '<i class="fas fa-chart-line"></i>' +
            '</button>' +
            '<button class="btn btn-sm btn-outline-secondary" onclick="etfSignalsManager.editSignal(\'' + signal.id + '\')" title="Edit Signal">' +
            '<i class="fas fa-edit"></i>' +
            '</button>';
        cells.push('<td>' + actionButtons + '</td>');
    }
    
    row.innerHTML = cells.join('');
    return row;
};

ETFSignalsManager.prototype.calculatePriceChange = function(entryPrice, currentPrice) {
    var entry = parseFloat(entryPrice) || 0;
    var current = parseFloat(currentPrice) || 0;
    return current - entry;
};

ETFSignalsManager.prototype.getStatusClass = function(status) {
    switch (status) {
        case 'ACTIVE': return 'bg-success';
        case 'EXECUTED': return 'bg-primary';
        case 'EXPIRED': return 'bg-warning';
        case 'CANCELLED': return 'bg-danger';
        default: return 'bg-secondary';
    }
};

ETFSignalsManager.prototype.updateCounts = function() {
    var visibleCount = document.getElementById('visibleSignalsCount');
    var showingCount = document.getElementById('showingCount');
    var totalCount = document.getElementById('totalCount');
    
    if (visibleCount) visibleCount.textContent = this.filteredSignals.length;
    if (totalCount) totalCount.textContent = this.signals.length;
    if (showingCount) {
        var startIndex = (this.currentPage - 1) * this.rowsPerPage;
        var endIndex = Math.min(startIndex + this.rowsPerPage, this.filteredSignals.length);
        showingCount.textContent = Math.max(0, endIndex - startIndex);
    }
};

ETFSignalsManager.prototype.updatePagination = function() {
    var totalPages = Math.ceil(this.filteredSignals.length / this.rowsPerPage);
    
    var currentPageSpan = document.getElementById('currentPage');
    var totalPagesSpan = document.getElementById('totalPages');
    var prevBtn = document.getElementById('prevBtn');
    var nextBtn = document.getElementById('nextBtn');
    
    if (currentPageSpan) currentPageSpan.textContent = this.currentPage;
    if (totalPagesSpan) totalPagesSpan.textContent = totalPages;
    
    if (prevBtn) {
        prevBtn.disabled = this.currentPage <= 1;
    }
    
    if (nextBtn) {
        nextBtn.disabled = this.currentPage >= totalPages;
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function() {
    var self = this;
    this.stopAutoRefresh();
    
    this.refreshInterval = setInterval(function() {
        if (!self.isRefreshing) {
            self.loadSignals();
        }
    }, this.refreshIntervalMs);
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};

ETFSignalsManager.prototype.showLoadingState = function(show) {
    var table = document.getElementById('signalsTable');
    if (table) {
        if (show) {
            table.style.opacity = '0.6';
        } else {
            table.style.opacity = '1';
        }
    }
};

ETFSignalsManager.prototype.showAlert = function(message, type) {
    var alertClass = 'alert-' + (type || 'info');
    var alertHtml = '<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        '</div>';
    
    var container = document.querySelector('.container-fluid');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        setTimeout(function() {
            var alert = document.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
};

ETFSignalsManager.prototype.updateColumnCheckboxes = function() {
    var container = document.getElementById('columnCheckboxes');
    if (!container) return;
    
    var columns = [
        { key: 'symbol', label: 'Symbol' },
        { key: 'signal_type', label: 'Signal Type' },
        { key: 'entry_price', label: 'Entry Price' },
        { key: 'current_price', label: 'Current Price' },
        { key: 'target_price', label: 'Target Price' },
        { key: 'stop_loss', label: 'Stop Loss' },
        { key: 'quantity', label: 'Quantity' },
        { key: 'investment_amount', label: 'Investment Amount' },
        { key: 'current_value', label: 'Current Value' },
        { key: 'pnl', label: 'P&L' },
        { key: 'pnl_percentage', label: 'P&L %' },
        { key: 'status', label: 'Status' },
        { key: 'created_at', label: 'Created At' },
        { key: 'actions', label: 'Actions' }
    ];
    
    container.innerHTML = '';
    var self = this;
    
    for (var i = 0; i < columns.length; i++) {
        var column = columns[i];
        var colDiv = document.createElement('div');
        colDiv.className = 'col-md-4 mb-2';
        
        var checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input';
        checkbox.id = 'col_' + column.key;
        checkbox.checked = this.visibleColumns[column.key];
        checkbox.setAttribute('data-column', column.key);
        
        var label = document.createElement('label');
        label.className = 'form-check-label text-light ms-2';
        label.setAttribute('for', 'col_' + column.key);
        label.textContent = column.label;
        
        var formCheck = document.createElement('div');
        formCheck.className = 'form-check';
        formCheck.appendChild(checkbox);
        formCheck.appendChild(label);
        
        colDiv.appendChild(formCheck);
        container.appendChild(colDiv);
    }
};

ETFSignalsManager.prototype.showTradeModal = function(signalId) {
    var signal = this.signals.find(function(s) { return s.id == signalId; });
    if (!signal) return;
    
    var tradeSymbol = document.getElementById('tradeSymbol');
    var tradeType = document.getElementById('tradeType');
    var tradePrice = document.getElementById('tradePrice');
    var tradeQuantity = document.getElementById('tradeQuantity');
    var targetPrice = document.getElementById('targetPrice');
    var stopLoss = document.getElementById('stopLoss');
    
    if (tradeSymbol) tradeSymbol.value = signal.symbol;
    if (tradeType) tradeType.value = signal.signal_type;
    if (tradePrice) tradePrice.value = signal.current_price;
    if (tradeQuantity) tradeQuantity.value = signal.quantity;
    if (targetPrice) targetPrice.value = signal.target_price;
    if (stopLoss) stopLoss.value = signal.stop_loss;
    
    var modal = document.getElementById('tradeModal');
    if (modal && typeof bootstrap !== 'undefined') {
        var bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
};

ETFSignalsManager.prototype.showChart = function(symbol) {
    var chartModalLabel = document.getElementById('chartModalLabel');
    if (chartModalLabel) {
        chartModalLabel.innerHTML = '<i class="fas fa-chart-line me-2"></i>ETF Price Chart - ' + symbol;
    }
    
    var modal = document.getElementById('chartModal');
    if (modal && typeof bootstrap !== 'undefined') {
        var bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
};

ETFSignalsManager.prototype.editSignal = function(signalId) {
    console.log('Edit signal:', signalId);
    // Implement edit functionality
};

// Global functions for button events
function refreshSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.loadSignals();
    }
}

function setRefreshInterval(intervalMs, displayText) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.refreshIntervalMs = intervalMs;
        window.etfSignalsManager.startAutoRefresh();
        
        var currentInterval = document.getElementById('currentInterval');
        if (currentInterval) {
            currentInterval.textContent = displayText;
        }
    }
}

function applyFilters() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.applyFilters();
        window.etfSignalsManager.renderTable();
        window.etfSignalsManager.updateCounts();
    }
}

function clearFilters() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.filters = {
            signalType: '',
            status: '',
            symbol: '',
            minPnl: '',
            maxPnl: ''
        };
        
        // Clear filter inputs
        var inputs = ['signalTypeFilter', 'statusFilter', 'symbolFilter', 'minPnlFilter', 'maxPnlFilter'];
        for (var i = 0; i < inputs.length; i++) {
            var element = document.getElementById(inputs[i]);
            if (element) element.value = '';
        }
        
        applyFilters();
    }
}

function applyColumnSettings() {
    if (window.etfSignalsManager) {
        var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
        for (var i = 0; i < checkboxes.length; i++) {
            var checkbox = checkboxes[i];
            var column = checkbox.getAttribute('data-column');
            window.etfSignalsManager.visibleColumns[column] = checkbox.checked;
        }
        
        window.etfSignalsManager.updateTableHeaders();
        window.etfSignalsManager.renderTable();
        
        var modal = bootstrap.Modal.getInstance(document.getElementById('columnSettingsModal'));
        if (modal) modal.hide();
    }
}

function selectAllColumns() {
    var checkboxes = document.querySelectorAll('#columnCheckboxes input[type="checkbox"]');
    for (var i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = true;
    }
}

function resetDefaultColumns() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.visibleColumns = {
            'symbol': true,
            'signal_type': true,
            'entry_price': true,
            'current_price': true,
            'pnl': true,
            'pnl_percentage': true,
            'status': true,
            'actions': true
        };
        window.etfSignalsManager.updateColumnCheckboxes();
    }
}

function previousPage() {
    if (window.etfSignalsManager && window.etfSignalsManager.currentPage > 1) {
        window.etfSignalsManager.currentPage--;
        window.etfSignalsManager.renderTable();
    }
}

function nextPage() {
    if (window.etfSignalsManager) {
        var totalPages = Math.ceil(window.etfSignalsManager.filteredSignals.length / window.etfSignalsManager.rowsPerPage);
        if (window.etfSignalsManager.currentPage < totalPages) {
            window.etfSignalsManager.currentPage++;
            window.etfSignalsManager.renderTable();
        }
    }
}

function exportSignals() {
    if (window.etfSignalsManager) {
        var csvContent = 'Symbol,Signal Type,Entry Price,Current Price,P&L,P&L %,Status\n';
        for (var i = 0; i < window.etfSignalsManager.signals.length; i++) {
            var signal = window.etfSignalsManager.signals[i];
            csvContent += [
                signal.symbol,
                signal.signal_type,
                signal.entry_price,
                signal.current_price,
                signal.pnl,
                signal.pnl_percentage,
                signal.status
            ].join(',') + '\n';
        }
        
        var blob = new Blob([csvContent], { type: 'text/csv' });
        var url = window.URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'etf_signals_' + new Date().toISOString().split('T')[0] + '.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

function submitTrade() {
    console.log('Submit trade functionality');
    // Implement trade submission
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.etfSignalsManager === 'undefined') {
        window.etfSignalsManager = new ETFSignalsManager();
    }
});

// Fallback initialization
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (typeof window.etfSignalsManager === 'undefined') {
        window.etfSignalsManager = new ETFSignalsManager();
    }
}
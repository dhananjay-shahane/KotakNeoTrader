// ETF Signals Manager - ES5 Compatible
function ETFSignalsManager() {
    this.positions = [];
    this.liveDataInterval = null;
    this.autoRefreshInterval = 10000; // 10 seconds
    this.searchTimeout = null;
    this.init();
}

ETFSignalsManager.prototype.init = function() {
    this.setupEventListeners();
    this.loadPositions();
    this.startAutoRefresh();
    this.initLiveDataConnection();
};

ETFSignalsManager.prototype.setupEventListeners = function() {
    var self = this;

    // Add deal button
    var addDealBtn = document.getElementById('addDealBtn');
    if (addDealBtn) {
        addDealBtn.addEventListener('click', function() {
            self.showAddDealModal();
        });
    }

    // Save position button
    var savePositionBtn = document.getElementById('savePositionBtn');
    if (savePositionBtn) {
        savePositionBtn.addEventListener('click', function() {
            self.savePosition();
        });
    }

    // Refresh button
    var refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            self.loadPositions();
        });
    }

    // Auto refresh interval change
    var autoRefreshInterval = document.getElementById('autoRefreshInterval');
    if (autoRefreshInterval) {
        autoRefreshInterval.addEventListener('change', function(e) {
            self.autoRefreshInterval = parseInt(e.target.value) * 1000;
            self.startAutoRefresh();
        });
    }

    // ETF symbol search
    var etfSymbol = document.getElementById('etfSymbol');
    if (etfSymbol) {
        etfSymbol.addEventListener('input', function(e) {
            clearTimeout(self.searchTimeout);
            self.searchTimeout = setTimeout(function() {
                self.searchETFSymbols(e.target.value);
            }, 300);
        });
    }

    // Position filters
    var positionFilter = document.getElementById('positionFilter');
    if (positionFilter) {
        positionFilter.addEventListener('change', function() {
            self.filterPositions();
        });
    }

    var statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            self.filterPositions();
        });
    }

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

    // Export buttons
    var exportCsvBtn = document.getElementById('exportCsvBtn');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', function() {
            self.exportToCSV();
        });
    }

    var exportPdfBtn = document.getElementById('exportPdfBtn');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', function() {
            self.exportToPDF();
        });
    }
};

ETFSignalsManager.prototype.loadPositions = function() {
    var self = this;
    this.showLoading(true);

    fetch('/api/etf/signals')
        .then(function(response) { 
            return response.json(); 
        })
        .then(function(data) {
            if (data.success) {
                self.positions = data.signals || [];
                self.renderPositionsTable();
                self.updateSummaryCards(data.portfolio || {});
                self.updateVisibleCount();
            } else {
                self.showAlert('Error loading positions: ' + (data.message || 'Unknown error'), 'error');
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            self.showAlert('Error loading positions: ' + error.message, 'error');
        })
        .finally(function() {
            self.showLoading(false);
        });
};

ETFSignalsManager.prototype.showLoading = function(show) {
    var loader = document.getElementById('loadingSpinner');
    if (loader) {
        loader.style.display = show ? 'block' : 'none';
    }
};

ETFSignalsManager.prototype.showAlert = function(message, type) {
    var alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
    var alertHtml = '<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        '</div>';
    
    var container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
    }

    // Auto remove after 5 seconds
    setTimeout(function() {
        var alert = document.querySelector('.alert:first-of-type');
        if (alert && alert.classList.contains(alertClass)) {
            alert.remove();
        }
    }, 5000);
};

ETFSignalsManager.prototype.renderPositionsTable = function() {
    var tbody = document.getElementById('positionsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';
    
    for (var i = 0; i < this.positions.length; i++) {
        var position = this.positions[i];
        var row = this.createPositionRow(position);
        tbody.appendChild(row);
    }
};

ETFSignalsManager.prototype.createPositionRow = function(position) {
    var row = document.createElement('tr');
    var pnlClass = (position.pnl || 0) >= 0 ? 'text-success' : 'text-danger';
    
    row.innerHTML = 
        '<td>' + (position.symbol || '') + '</td>' +
        '<td>' + (position.signal_type || '') + '</td>' +
        '<td>₹' + (position.entry_price || 0).toFixed(2) + '</td>' +
        '<td>₹' + (position.current_price || 0).toFixed(2) + '</td>' +
        '<td class="' + pnlClass + '">₹' + (position.pnl || 0).toFixed(2) + '</td>' +
        '<td>' + (position.quantity || 0) + '</td>' +
        '<td>' + (position.status || '') + '</td>' +
        '<td>' +
        '<button class="btn btn-sm btn-outline-primary me-1" onclick="etfSignalsManager.editPosition(' + position.id + ')">Edit</button>' +
        '<button class="btn btn-sm btn-outline-danger" onclick="etfSignalsManager.deletePosition(' + position.id + ')">Delete</button>' +
        '</td>';
    
    return row;
};

ETFSignalsManager.prototype.updateSummaryCards = function(portfolio) {
    var totalValue = document.getElementById('totalValue');
    var totalPnl = document.getElementById('totalPnl');
    var totalPositions = document.getElementById('totalPositions');

    if (totalValue && portfolio.total_value !== undefined) {
        totalValue.textContent = '₹' + portfolio.total_value.toFixed(2);
    }

    if (totalPnl && portfolio.total_pnl !== undefined) {
        totalPnl.textContent = '₹' + portfolio.total_pnl.toFixed(2);
        totalPnl.className = portfolio.total_pnl >= 0 ? 'text-success' : 'text-danger';
    }

    if (totalPositions && portfolio.total_positions !== undefined) {
        totalPositions.textContent = portfolio.total_positions;
    }
};

ETFSignalsManager.prototype.updateVisibleCount = function() {
    var countElement = document.getElementById('visibleCount');
    if (countElement) {
        countElement.textContent = this.positions.length;
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function() {
    var self = this;
    this.stopAutoRefresh();
    
    this.liveDataInterval = setInterval(function() {
        self.loadPositions();
    }, this.autoRefreshInterval);
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.liveDataInterval) {
        clearInterval(this.liveDataInterval);
        this.liveDataInterval = null;
    }
};

ETFSignalsManager.prototype.initLiveDataConnection = function() {
    // Placeholder for WebSocket connection
    console.log('Live data connection initialized');
};

ETFSignalsManager.prototype.showAddDealModal = function() {
    var modal = document.getElementById('addDealModal');
    if (modal && typeof bootstrap !== 'undefined') {
        var bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
};

ETFSignalsManager.prototype.savePosition = function() {
    // Placeholder for save position functionality
    console.log('Save position called');
};

ETFSignalsManager.prototype.searchETFSymbols = function(query) {
    // Placeholder for ETF symbol search
    console.log('Searching ETF symbols:', query);
};

ETFSignalsManager.prototype.filterPositions = function() {
    // Placeholder for position filtering
    console.log('Filtering positions');
};

ETFSignalsManager.prototype.editPosition = function(id) {
    console.log('Edit position:', id);
};

ETFSignalsManager.prototype.deletePosition = function(id) {
    console.log('Delete position:', id);
};

ETFSignalsManager.prototype.exportToCSV = function() {
    console.log('Export to CSV');
};

ETFSignalsManager.prototype.exportToPDF = function() {
    console.log('Export to PDF');
};

// Initialize ETF Signals Manager when DOM is ready
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
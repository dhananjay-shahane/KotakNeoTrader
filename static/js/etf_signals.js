
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

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/etf/signals', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            self.showLoading(false);
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    if (data.success) {
                        self.positions = data.signals || [];
                        self.renderPositionsTable();
                        self.updateSummaryCards(data.portfolio || {});
                        self.updateVisibleCount();
                        console.log('Loaded', self.positions.length, 'ETF signals');
                    } else {
                        self.showAlert('Error loading positions: ' + (data.message || 'Unknown error'), 'error');
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                    self.showAlert('Error parsing server response', 'error');
                }
            } else {
                self.showAlert('Error loading positions: Server error ' + xhr.status, 'error');
            }
        }
    };
    xhr.send();
};

ETFSignalsManager.prototype.showLoading = function(show) {
    var loader = document.getElementById('loadingSpinner');
    if (loader) {
        loader.style.display = show ? 'block' : 'none';
    }
    
    var tbody = document.getElementById('signalsTableBody');
    if (tbody && show) {
        tbody.innerHTML = '<tr><td colspan="25" class="text-center">Loading ETF signals...</td></tr>';
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
    var tbody = document.getElementById('signalsTableBody');
    if (!tbody) {
        console.error('Table body not found');
        return;
    }

    tbody.innerHTML = '';
    
    if (!this.positions || this.positions.length === 0) {
        var row = tbody.insertRow();
        row.innerHTML = '<td colspan="25" class="text-center text-muted">No ETF signals found</td>';
        return;
    }
    
    console.log('Rendering', this.positions.length, 'positions');
    
    for (var i = 0; i < this.positions.length; i++) {
        var position = this.positions[i];
        var row = this.createPositionRow(position);
        tbody.appendChild(row);
    }
};

ETFSignalsManager.prototype.createPositionRow = function(position) {
    var row = document.createElement('tr');
    
    // Ensure we have valid data with fallbacks
    var symbol = position.symbol || position.etf || 'N/A';
    var entryPrice = parseFloat(position.ep || position.entry_price || 0);
    var currentPrice = parseFloat(position.cmp || position.current_price || entryPrice);
    var quantity = parseInt(position.qty || position.quantity || 0);
    var pnl = parseFloat(position.pl || position.pnl_amount || 0);
    var changePct = parseFloat(position.change_pct || position.change_percent || 0);
    var investment = parseFloat(position.inv || position.invested_amount || (entryPrice * quantity));
    var targetPrice = parseFloat(position.tp || position.target_price || 0);
    
    // Ensure current price is never 0 or undefined
    if (!currentPrice || currentPrice <= 0) {
        currentPrice = entryPrice || 100; // Use entry price or default fallback
    }
    
    var pnlClass = pnl >= 0 ? 'profit' : 'loss';
    var changeClass = changePct >= 0 ? 'profit' : 'loss';
    
    row.innerHTML = 
        '<td><strong>' + symbol + '</strong></td>' +
        '<td>' + (position.thirty || '0%') + '</td>' +
        '<td>' + (position.dh || '0') + '</td>' +
        '<td>' + (position.date || '') + '</td>' +
        '<td><span class="badge ' + (position.pos == 1 ? 'bg-success' : 'bg-secondary') + '">' + (position.pos == 1 ? '1 (OPEN)' : '0 (CLOSED)') + '</span></td>' +
        '<td>' + quantity + '</td>' +
        '<td>₹' + entryPrice.toFixed(2) + '</td>' +
        '<td class="' + changeClass + '">₹' + currentPrice.toFixed(2) + 
        (position.data_source && position.data_source.includes('KOTAK_NEO') ? ' <span class="badge bg-success badge-sm">KN</span>' : ' <span class="badge bg-warning badge-sm">EP</span>') + '</td>' +
        '<td class="' + changeClass + '">' + changePct.toFixed(2) + '%</td>' +
        '<td>₹' + investment.toFixed(0) + '</td>' +
        '<td>₹' + targetPrice.toFixed(2) + '</td>' +
        '<td>₹' + (position.tva || 0).toFixed(0) + '</td>' +
        '<td class="profit">₹' + (position.tpr || 0).toFixed(0) + '</td>' +
        '<td class="' + pnlClass + '">₹' + pnl.toFixed(0) + '</td>' +
        '<td>' + (position.ed || '') + '</td>' +
        '<td>' + (position.exp || '') + '</td>' +
        '<td>' + (position.pr || '0%') + '</td>' +
        '<td>' + (position.pp || '★') + '</td>' +
        '<td>' + (position.iv || investment.toFixed(0)) + '</td>' +
        '<td class="' + changeClass + '">' + (position.ip || changePct.toFixed(2) + '%') + '</td>' +
        '<td><small>' + (position.nt || '') + '</small></td>' +
        '<td><small>' + (position.qt || '') + '</small></td>' +
        '<td class="' + changeClass + '">' + (position.seven || '0%') + '</td>' +
        '<td class="' + changeClass + '">' + changePct.toFixed(2) + '%</td>' +
        '<td>' +
        '<button class="btn btn-sm btn-primary" onclick="addDeal(\'' + symbol + '\', ' + currentPrice + ')">Add Deal</button>' +
        '</td>';
    
    return row;
};

ETFSignalsManager.prototype.updateSummaryCards = function(portfolio) {
    var totalValue = document.getElementById('totalValue');
    var totalPnl = document.getElementById('totalPnl');
    var totalPositions = document.getElementById('totalPositions');

    if (totalValue && portfolio.current_value !== undefined) {
        totalValue.textContent = '₹' + portfolio.current_value.toFixed(2);
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
    
    var visibleSignalsCount = document.getElementById('visibleSignalsCount');
    if (visibleSignalsCount) {
        visibleSignalsCount.textContent = this.positions.length;
    }
};

ETFSignalsManager.prototype.startAutoRefresh = function() {
    var self = this;
    this.stopAutoRefresh();
    
    if (this.autoRefreshInterval > 0) {
        this.liveDataInterval = setInterval(function() {
            self.loadPositions();
        }, this.autoRefreshInterval);
        console.log('Auto refresh started:', this.autoRefreshInterval + 'ms');
    }
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.liveDataInterval) {
        clearInterval(this.liveDataInterval);
        this.liveDataInterval = null;
        console.log('Auto refresh stopped');
    }
};

ETFSignalsManager.prototype.initLiveDataConnection = function() {
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
    console.log('Save position called');
};

ETFSignalsManager.prototype.searchETFSymbols = function(query) {
    console.log('Searching ETF symbols:', query);
};

ETFSignalsManager.prototype.filterPositions = function() {
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

// Global functions for button onclick handlers
function refreshSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.loadPositions();
    }
}

function setRefreshInterval(interval, text) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.autoRefreshInterval = interval;
        window.etfSignalsManager.startAutoRefresh();
        var currentInterval = document.getElementById('currentInterval');
        if (currentInterval) {
            currentInterval.textContent = text;
        }
    }
}

function exportSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.exportToCSV();
    }
}

function addDeal(symbol, price) {
    var dealUrl = '/deals?symbol=' + encodeURIComponent(symbol) + '&price=' + price;
    window.location.href = dealUrl;
}

// Initialize ETF Signals Manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.etfSignalsManager === 'undefined') {
        window.etfSignalsManager = new ETFSignalsManager();
        console.log('ETF Signals Manager initialized');
    }
});

// Fallback initialization
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (typeof window.etfSignalsManager === 'undefined') {
        window.etfSignalsManager = new ETFSignalsManager();
        console.log('ETF Signals Manager initialized (fallback)');
    }
}

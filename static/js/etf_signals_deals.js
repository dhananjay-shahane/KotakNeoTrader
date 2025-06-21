// ETF Signals Manager - Matching Deals Page Structure Exactly
function ETFSignalsManager() {
    this.signals = [];
    this.filteredSignals = [];
    this.currentPage = 1;
    this.pageSize = 20;
    this.autoRefresh = true;
    this.refreshInterval = null;
    this.refreshIntervalTime = 30000; // Default 30 seconds
    this.searchTimeout = null;

    // Available columns configuration (matching deals page exactly)
    this.availableColumns = {
        'symbol': { label: 'Symbol', default: true, width: '70px' },
        'thirty': { label: '30', default: false, width: '50px' },
        'dh': { label: 'DH', default: true, width: '50px' },
        'date': { label: 'Date', default: true, width: '70px' },
        'pos': { label: 'Pos', default: true, width: '50px' },
        'qty': { label: 'Qty', default: true, width: '50px' },
        'ep': { label: 'EP', default: true, width: '70px' },
        'cmp': { label: 'CMP', default: true, width: '70px' },
        'change_pct': { label: '%Chan', default: true, width: '60px' },
        'inv': { label: 'Inv.', default: true, width: '70px' },
        'tp': { label: 'TP', default: true, width: '60px' },
        'tva': { label: 'TVA', default: true, width: '70px' },
        'tpr': { label: 'TPR', default: true, width: '70px' },
        'pl': { label: 'PL', default: true, width: '60px' },
        'ed': { label: 'ED', default: false, width: '70px' },
        'pr': { label: 'PR', default: true, width: '80px' },
        'pp': { label: 'PP', default: true, width: '50px' },
        'iv': { label: 'IV', default: true, width: '60px' },
        'ip': { label: 'IP', default: true, width: '60px' },
        'nt': { label: 'NT', default: false, width: '60px' },
        'qt': { label: 'Qt', default: false, width: '60px' },
        'seven': { label: '7', default: false, width: '50px' },
        'change2': { label: '%Ch', default: false, width: '60px' },
        'actions': { label: 'Actions', default: true, width: '80px' }
    };

    this.selectedColumns = this.getDefaultColumns();
    this.init();
}

ETFSignalsManager.prototype.getDefaultColumns = function() {
    var self = this;
    return Object.keys(this.availableColumns).filter(function(col) {
        return self.availableColumns[col].default;
    });
};

ETFSignalsManager.prototype.init = function() {
    this.generateColumnCheckboxes();
    this.updateTableHeaders();
    this.loadSignals();
    this.startAutoRefresh();
    this.setupEventListeners();

    // Auto refresh toggle
    var autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        var self = this;
        autoRefreshToggle.addEventListener('change', function(e) {
            self.autoRefresh = e.target.checked;
            if (self.autoRefresh) {
                self.startAutoRefresh();
            } else {
                self.stopAutoRefresh();
            }
        });
    }
};

ETFSignalsManager.prototype.generateColumnCheckboxes = function() {
    var container = document.getElementById('columnCheckboxes');
    if (!container) return;

    container.innerHTML = '';
    var self = this;

    Object.keys(this.availableColumns).forEach(function(column) {
        var colInfo = self.availableColumns[column];
        var colDiv = document.createElement('div');
        colDiv.className = 'col-md-4 col-lg-3 mb-2';

        colDiv.innerHTML = 
            '<div class="form-check">' +
                '<input class="form-check-input" type="checkbox" id="col_' + column + '" ' +
                (self.selectedColumns.indexOf(column) !== -1 ? 'checked' : '') + '>' +
                '<label class="form-check-label text-light" for="col_' + column + '">' +
                    colInfo.label +
                '</label>' +
            '</div>';

        container.appendChild(colDiv);
    });
};

ETFSignalsManager.prototype.updateTableHeaders = function() {
    var headersRow = document.getElementById('tableHeaders');
    if (!headersRow) return;

    headersRow.innerHTML = '';
    var self = this;

    this.selectedColumns.forEach(function(column) {
        var th = document.createElement('th');
        var colInfo = self.availableColumns[column];
        th.style.width = colInfo.width;
        th.className = 'text-center';
        th.style.backgroundColor = 'var(--secondary-color)';
        th.style.color = 'var(--text-primary)';
        th.style.fontWeight = '600';
        th.style.fontSize = '0.7rem';
        th.style.padding = '6px 3px';
        th.style.border = '1px solid var(--border-color)';
        th.style.position = 'sticky';
        th.style.top = '0';
        th.style.zIndex = '10';
        th.style.whiteSpace = 'nowrap';
        th.textContent = colInfo.label;
        th.title = self.getColumnTooltip(column);
        headersRow.appendChild(th);
    });
};

ETFSignalsManager.prototype.getColumnTooltip = function(column) {
    var tooltips = {
        'symbol': 'Trading Symbol',
        'thirty': '30 Day Performance',
        'dh': 'Days Held',
        'date': 'Signal Date',
        'pos': 'Position Type',
        'qty': 'Quantity',
        'ep': 'Entry Price',
        'cmp': 'Current Market Price',
        'change_pct': 'Percentage Change',
        'inv': 'Investment Amount',
        'tp': 'Target Price',
        'tva': 'Target Value Amount',
        'tpr': 'Target Profit Return',
        'pl': 'Profit/Loss',
        'ed': 'Entry Date',
        'pr': 'Price Range',
        'pp': 'Performance Points',
        'iv': 'Implied Volatility',
        'ip': 'Intraday Performance',
        'nt': 'Notes/Tags',
        'qt': 'Quote Time',
        'seven': '7 Day Change',
        'change2': 'Percentage Change',
        'actions': 'Actions'
    };
    return tooltips[column] || column.toUpperCase();
};

ETFSignalsManager.prototype.setupEventListeners = function() {
    // Filter event listeners can be added here
};

ETFSignalsManager.prototype.loadSignals = function() {
    var self = this;
    try {
        // Load ETF signals data from API and format it like deals
        fetch('/api/etf-signals-data')
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    self.signals = data.signals || [];
                    self.filteredSignals = self.signals.slice();
                    self.renderSignalsTable();
                    self.updatePagination();
                } else {
                    self.showError('Failed to load ETF signals data');
                }
            })
            .catch(function(error) {
                console.error('Error loading signals:', error);
                self.showError('Failed to load ETF signals data');
            });
    } catch (error) {
        console.error('Error loading signals:', error);
        this.showError('Failed to load signals data');
    }
};



ETFSignalsManager.prototype.renderSignalsTable = function() {
    var tbody = document.getElementById('signalsTableBody');
    if (!tbody) return;

    var startIndex = (this.currentPage - 1) * this.pageSize;
    var endIndex = startIndex + this.pageSize;
    var pageSignals = this.filteredSignals.slice(startIndex, endIndex);

    tbody.innerHTML = '';

    if (pageSignals.length === 0) {
        var row = document.createElement('tr');
        row.innerHTML = 
            '<td colspan="' + this.selectedColumns.length + '" class="text-center py-4">' +
                '<i class="fas fa-chart-line fa-3x mb-3 text-primary"></i>' +
                '<h6 class="text-light">No ETF Signals Found</h6>' +
                '<p class="text-muted mb-0">No ETF trading signals available</p>' +
                '<small class="text-muted">Signals will appear here when available</small>' +
            '</td>';
        tbody.appendChild(row);
        return;
    }

    var self = this;
    pageSignals.forEach(function(signal) {
        var row = document.createElement('tr');

        self.selectedColumns.forEach(function(columnKey) {
            var cell = document.createElement('td');
            cell.className = 'text-center';
            cell.style.padding = '4px 3px';
            cell.style.border = '1px solid var(--border-color)';
            cell.style.fontSize = '0.75rem';

            var cellContent = '';
            var bgColor = '';

            switch(columnKey) {
                case 'symbol':
                    cellContent = '<strong>' + (signal.symbol || '') + '</strong>';
                    break;
                case 'thirty':
                    cellContent = signal.thirty || '-';
                    break;
                case 'dh':
                    cellContent = signal.dh !== undefined ? signal.dh + 'd' : '0d';
                    break;
                case 'date':
                    cellContent = signal.date || '';
                    break;
                case 'pos':
                    cellContent = '<span class="badge ' + (signal.pos === 1 ? 'bg-success' : 'bg-danger') + '">' + signal.pos + '</span>';
                    break;
                case 'qty':
                    cellContent = signal.qty ? signal.qty.toLocaleString('en-IN') : '';
                    break;
                case 'ep':
                    cellContent = signal.ep ? '₹' + signal.ep.toFixed(2) : '';
                    break;
                case 'cmp':
                    cellContent = signal.cmp ? '₹' + signal.cmp.toFixed(2) : '';
                    break;
                case 'change_pct':
                    if (signal.change_pct !== undefined) {
                        bgColor = signal.change_pct >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
                        cellContent = (signal.change_pct >= 0 ? '+' : '') + signal.change_pct.toFixed(2) + '%';
                    }
                    break;
                case 'inv':
                    cellContent = signal.inv ? '₹' + signal.inv.toLocaleString('en-IN') : '';
                    break;
                case 'tp':
                    cellContent = signal.tp ? '₹' + signal.tp.toFixed(2) : '-';
                    break;
                case 'tva':
                    cellContent = signal.tva ? '₹' + signal.tva.toLocaleString('en-IN') : '';
                    break;
                case 'tpr':
                    cellContent = signal.tpr ? '₹' + signal.tpr.toFixed(0) : '0';
                    break;
                case 'pl':
                    if (signal.pl !== undefined) {
                        bgColor = signal.pl >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
                        cellContent = '₹' + (signal.pl >= 0 ? '+' : '') + signal.pl.toFixed(0);
                    }
                    break;
                case 'ed':
                    cellContent = signal.ed || '';
                    break;
                case 'pr':
                    cellContent = signal.pr || '-';
                    break;
                case 'pp':
                    cellContent = signal.pp || '-';
                    break;
                case 'iv':
                    cellContent = '<span class="badge bg-info">' + (signal.iv || 'Low') + '</span>';
                    break;
                case 'ip':
                    cellContent = signal.ip || '-';
                    if (signal.change_pct > 0) {
                        cell.style.color = 'var(--success-color)';
                    } else if (signal.change_pct < 0) {
                        cell.style.color = 'var(--danger-color)';
                    }
                    break;
                case 'nt':
                    cellContent = '<small>' + (signal.nt || '-') + '</small>';
                    break;
                case 'qt':
                    cellContent = '<small>' + (signal.qt || '-') + '</small>';
                    break;
                case 'seven':
                    cellContent = signal.seven || '-';
                    break;
                case 'change2':
                    if (signal.change2 !== undefined) {
                        bgColor = signal.change2 >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
                        cellContent = (signal.change2 >= 0 ? '+' : '') + signal.change2.toFixed(2) + '%';
                    }
                    break;
                case 'actions':
                    cellContent = 
                        '<button class="btn btn-sm btn-primary" onclick="addDeal(\'' + signal.symbol + '\', ' + signal.cmp + ')" title="Add Deal">' +
                            '<i class="fas fa-plus me-1"></i>Add Deal' +
                        '</button>';
                    break;
                default:
                    cellContent = '';
            }

            if (bgColor) {
                cell.style.backgroundColor = bgColor;
                cell.style.color = 'white';
                cell.style.fontWeight = 'bold';
            }

            cell.innerHTML = cellContent;
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    document.getElementById('visibleSignalsCount').textContent = this.filteredSignals.length;
    document.getElementById('showingCount').textContent = Math.min(endIndex, this.filteredSignals.length);
    document.getElementById('totalCount').textContent = this.filteredSignals.length;
};

ETFSignalsManager.prototype.updatePagination = function() {
    var totalPages = Math.ceil(this.filteredSignals.length / this.pageSize);

    document.getElementById('currentPage').textContent = this.currentPage;
    document.getElementById('totalPages').textContent = totalPages;

    document.getElementById('prevBtn').disabled = this.currentPage <= 1;
    document.getElementById('nextBtn').disabled = this.currentPage >= totalPages;
};

ETFSignalsManager.prototype.startAutoRefresh = function() {
    var self = this;
    if (this.refreshInterval) clearInterval(this.refreshInterval);
    if (this.autoRefresh) {
        this.refreshInterval = setInterval(function() {
            self.loadSignals();
        }, this.refreshIntervalTime);
    }
};

ETFSignalsManager.prototype.stopAutoRefresh = function() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
    }
};

ETFSignalsManager.prototype.showError = function(message) {
    var tbody = document.getElementById('signalsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = 
        '<tr>' +
            '<td colspan="' + this.selectedColumns.length + '" class="text-center py-4">' +
                '<i class="fas fa-exclamation-triangle fa-3x mb-3 text-danger"></i>' +
                '<h6 class="text-danger">' + message + '</h6>' +
                '<button class="btn btn-outline-primary btn-sm mt-2" onclick="window.etfSignalsManager.loadSignals()">' +
                    '<i class="fas fa-sync me-1"></i>Retry' +
                '</button>' +
            '</td>' +
        '</tr>';
};

// Global functions for column settings and filters
function applyColumnSettings() {
    if (!window.etfSignalsManager) return;
    
    window.etfSignalsManager.selectedColumns = [];

    Object.keys(window.etfSignalsManager.availableColumns).forEach(function(column) {
        var checkbox = document.getElementById('col_' + column);
        if (checkbox && checkbox.checked) {
            window.etfSignalsManager.selectedColumns.push(column);
        }
    });

    window.etfSignalsManager.updateTableHeaders();
    window.etfSignalsManager.renderSignalsTable();

    var modal = bootstrap.Modal.getInstance(document.getElementById('columnSettingsModal'));
    if (modal) modal.hide();
}

function selectAllColumns() {
    if (!window.etfSignalsManager) return;
    
    Object.keys(window.etfSignalsManager.availableColumns).forEach(function(column) {
        var checkbox = document.getElementById('col_' + column);
        if (checkbox) checkbox.checked = true;
    });
}

function resetDefaultColumns() {
    if (!window.etfSignalsManager) return;
    
    Object.keys(window.etfSignalsManager.availableColumns).forEach(function(column) {
        var checkbox = document.getElementById('col_' + column);
        if (checkbox) {
            checkbox.checked = window.etfSignalsManager.availableColumns[column].default;
        }
    });
}

function applyFilters() {
    if (!window.etfSignalsManager) return;
    
    var orderType = document.getElementById('orderTypeFilter').value;
    var status = document.getElementById('statusFilter').value;
    var symbol = document.getElementById('symbolFilter').value.toLowerCase();
    var minPnl = parseFloat(document.getElementById('minPnlFilter').value) || -Infinity;
    var maxPnl = parseFloat(document.getElementById('maxPnlFilter').value) || Infinity;

    window.etfSignalsManager.filteredSignals = window.etfSignalsManager.signals.filter(function(signal) {
        var matchesOrderType = !orderType || (orderType === 'BUY' && signal.pos === 1) || (orderType === 'SELL' && signal.pos === 0);
        var matchesStatus = !status || signal.status === status;
        var matchesSymbol = !symbol || signal.symbol.toLowerCase().indexOf(symbol) !== -1;
        var matchesPnl = signal.pl >= minPnl && signal.pl <= maxPnl;

        return matchesOrderType && matchesStatus && matchesSymbol && matchesPnl;
    });

    window.etfSignalsManager.currentPage = 1;
    window.etfSignalsManager.renderSignalsTable();
    window.etfSignalsManager.updatePagination();
}

function clearFilters() {
    document.getElementById('orderTypeFilter').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('symbolFilter').value = '';
    document.getElementById('minPnlFilter').value = '';
    document.getElementById('maxPnlFilter').value = '';

    if (window.etfSignalsManager) {
        window.etfSignalsManager.filteredSignals = window.etfSignalsManager.signals.slice();
        window.etfSignalsManager.currentPage = 1;
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();
    }
}

function refreshSignals() {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.loadSignals();
    }
}

function previousPage() {
    if (window.etfSignalsManager && window.etfSignalsManager.currentPage > 1) {
        window.etfSignalsManager.currentPage--;
        window.etfSignalsManager.renderSignalsTable();
        window.etfSignalsManager.updatePagination();
    }
}

function nextPage() {
    if (window.etfSignalsManager) {
        var totalPages = Math.ceil(window.etfSignalsManager.filteredSignals.length / window.etfSignalsManager.pageSize);
        if (window.etfSignalsManager.currentPage < totalPages) {
            window.etfSignalsManager.currentPage++;
            window.etfSignalsManager.renderSignalsTable();
            window.etfSignalsManager.updatePagination();
        }
    }
}

function setRefreshInterval(intervalMs, displayText) {
    if (window.etfSignalsManager) {
        window.etfSignalsManager.refreshIntervalTime = intervalMs;
        window.etfSignalsManager.startAutoRefresh();
        
        var currentInterval = document.getElementById('currentInterval');
        if (currentInterval) {
            currentInterval.textContent = displayText;
        }
    }
}

function exportSignals() {
    if (!window.etfSignalsManager) return;
    
    var csvContent = 'Symbol,Position,Quantity,Entry Price,Current Price,P&L,P&L %,Status\n';
    window.etfSignalsManager.signals.forEach(function(signal) {
        csvContent += [
            signal.symbol,
            signal.pos === 1 ? 'BUY' : 'SELL',
            signal.qty,
            signal.ep,
            signal.cmp,
            signal.pl,
            signal.change_pct,
            signal.status
        ].join(',') + '\n';
    });
    
    var blob = new Blob([csvContent], { type: 'text/csv' });
    var url = window.URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'etf_signals_' + new Date().toISOString().split('T')[0] + '.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

function addDeal(symbol, price) {
    alert('Add Deal functionality for ' + symbol + ' at ₹' + price.toFixed(2));
    // Implement add deal functionality here
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
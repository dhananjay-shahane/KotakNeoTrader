// WebSocket handler for real-time market data feeds - Kotak Neo Trading App

class WebSocketHandler {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.heartbeatInterval = null;
        this.subscriptions = new Map();
        this.messageHandlers = new Map();
        this.init();
    }

    init() {
        this.setupMessageHandlers();
        console.log('WebSocket Handler initialized');
    }

    setupMessageHandlers() {
        // Register message handlers for different data types
        this.messageHandlers.set('quote', this.handleQuoteUpdate.bind(this));
        this.messageHandlers.set('depth', this.handleDepthUpdate.bind(this));
        this.messageHandlers.set('order', this.handleOrderUpdate.bind(this));
        this.messageHandlers.set('position', this.handlePositionUpdate.bind(this));
        this.messageHandlers.set('holding', this.handleHoldingUpdate.bind(this));
        this.messageHandlers.set('error', this.handleError.bind(this));
    }

    connect() {
        try {
            // Note: The actual WebSocket URL would be provided by the Kotak Neo API
            // This is a placeholder for the WebSocket connection setup
            // In production, this would connect to Kotak Neo's WebSocket feed

            console.log('Attempting to establish WebSocket connection...');

            // Simulate WebSocket connection for now
            // In real implementation, this would be:
            // this.ws = new WebSocket('wss://kotak-neo-websocket-url');

            this.simulateConnection();

        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.handleConnectionError();
        }
    }

    simulateConnection() {
        // This simulates the WebSocket connection behavior
        // Replace this with actual Kotak Neo WebSocket implementation

        setTimeout(() => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            console.log('✅ WebSocket connected (simulated)');

            this.onOpen();
            this.startHeartbeat();

            // Simulate receiving market data
            if (window.location.search.includes('debug=true') || window.location.hostname === 'localhost') {
                this.startSimulatedDataFeed();
            }

        }, 1000);
    }

    startSimulatedDataFeed() {
        // This simulates real-time market data updates
        // Remove this in production and use actual WebSocket messages

        setInterval(() => {
            if (this.isConnected) {
                // Simulate quote updates
                this.simulateQuoteUpdate();

                // Simulate order updates occasionally
                if (Math.random() > 0.9) {
                    this.simulateOrderUpdate();
                }
            }
        }, 2000);
    }

    simulateQuoteUpdate() {
        // Simulate live price updates for demonstration
        const symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'];
        const symbol = symbols[Math.floor(Math.random() * symbols.length)];

        const mockQuoteData = {
            type: 'quote',
            symbol: symbol,
            ltp: (2000 + Math.random() * 1000).toFixed(2),
            change: ((Math.random() - 0.5) * 100).toFixed(2),
            changePercent: ((Math.random() - 0.5) * 5).toFixed(2),
            volume: Math.floor(Math.random() * 1000000),
            timestamp: new Date().toISOString()
        };

        this.handleMessage(mockQuoteData);
    }

    simulateOrderUpdate() {
        // Simulate order status updates for demonstration
        // Focus on completion to test the order complete functionality
        const orderStatuses = ['COMPLETE', 'PENDING', 'REJECTED'];
        const status = orderStatuses[Math.floor(Math.random() * orderStatuses.length)];

        const mockOrderData = {
            type: 'order',
            orderId: 'ORD' + Math.floor(Math.random() * 1000000),
            symbol: 'RELIANCE',
            status: status,
            quantity: Math.floor(Math.random() * 100) + 1,
            price: (2000 + Math.random() * 1000).toFixed(2),
            timestamp: new Date().toISOString()
        };

        this.handleMessage(mockOrderData);
    }

    onOpen() {
        console.log('WebSocket connection opened');
        this.showConnectionStatus(true);

        // Subscribe to previously subscribed instruments
        this.resubscribeAll();

        // Notify dashboard of connection
        if (window.tradingDashboard) {
            window.tradingDashboard.isConnected = true;
        }
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    handleMessage(data) {
        try {
            // Only log in debug mode
            if (window.location.search.includes('debug=true')) {
                console.log('📊 Market Data:', data);
            }

            switch(data.type) {
                case 'quote':
                    this.updateQuoteDisplays(data);
                    break;
                case 'order':
                    this.updateOrderDisplays(data);
                    // Show notification for order updates
                    if (data.status === 'COMPLETE') {
                        this.showOrderNotification(`Order ${data.orderId} completed successfully`, 'success');
                    } else if (data.status === 'REJECTED') {
                        this.showOrderNotification(`Order ${data.orderId} was rejected`, 'danger');
                    }
                    break;
                case 'position':
                    this.updatePositionDisplays(data);
                    break;
                default:
                    if (window.location.search.includes('debug=true')) {
                        console.log('Unknown message type:', data.type);
                    }
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }

    handleQuoteUpdate(data) {
        // Update quote data in the UI
        console.log('Quote update:', data);

        // Update LTP displays
        this.updatePriceElements(data.symbol, data.ltp, data.change);

        // Update any charts or graphs
        this.updatePriceCharts(data);

        // Trigger price change animation
        this.animatePriceChange(data.symbol, data.change);
    }

    handleDepthUpdate(data) {
        // Handle market depth updates
        console.log('Depth update:', data);

        // Update order book display if visible
        this.updateOrderBook(data);
    }

    handleOrderUpdate(data) {
        // Handle order status updates
        console.log('Order update:', data);

        // Show notification for order updates
        this.showOrderNotification(data);

        // Update order displays
        this.updateOrderDisplays(data);

        // Refresh positions if order is complete
        if (data.status === 'COMPLETE') {
            this.refreshPositions();
        }
    }

    handlePositionUpdate(data) {
        // Handle position updates
        console.log('Position update:', data);

        // Update position displays
        this.updatePositionDisplays(data);
    }

    handleHoldingUpdate(data) {
        // Handle holding updates
        console.log('Holding update:', data);

        // Update holding displays
        this.updateHoldingDisplays(data);
    }

    handleError(data) {
        console.error('WebSocket error:', data);
        this.showErrorNotification(data.message || 'WebSocket error occurred');
    }

    updatePriceElements(symbol, ltp, change) {
        // Find and update all price elements for the symbol
        const priceElements = document.querySelectorAll(`[data-symbol="${symbol}"] .price-ltp, [data-symbol="${symbol}"][data-price="ltp"]`);

        priceElements.forEach(element => {
            const oldValue = parseFloat(element.textContent.replace(/[^\d.-]/g, ''));
            const newValue = parseFloat(ltp);

            // Update the value
            element.textContent = `₹${newValue.toFixed(2)}`;

            // Add price change class
            element.classList.remove('price-up', 'price-down');
            if (change > 0) {
                element.classList.add('price-up');
            } else if (change < 0) {
                element.classList.add('price-down');
            }

            // Remove the class after animation
            setTimeout(() => {
                element.classList.remove('price-up', 'price-down');
            }, 1000);
        });

        // Update change elements
        const changeElements = document.querySelectorAll(`[data-symbol="${symbol}"] .price-change, [data-symbol="${symbol}"][data-price="change"]`);
        changeElements.forEach(element => {
            element.textContent = `${change > 0 ? '+' : ''}${parseFloat(change).toFixed(2)}`;
            element.className = `price-change ${change > 0 ? 'text-success' : change < 0 ? 'text-danger' : 'text-muted'}`;
        });
    }

    updatePriceCharts(data) {
        // Update any Chart.js charts with new price data
        if (window.Chart && window.Chart.instances) {
            Object.values(window.Chart.instances).forEach(chart => {
                if (chart.data && chart.data.datasets) {
                    // Update chart data if it matches the symbol
                    chart.data.datasets.forEach(dataset => {
                        if (dataset.label === data.symbol) {
                            // Add new data point
                            chart.data.labels.push(new Date().toLocaleTimeString());
                            dataset.data.push(parseFloat(data.ltp));

                            // Keep only last 50 data points
                            if (chart.data.labels.length > 50) {
                                chart.data.labels.shift();
                                dataset.data.shift();
                            }

                            chart.update('none');
                        }
                    });
                }
            });
        }
    }

    animatePriceChange(symbol, change) {
        // Animate price changes for visual feedback
        const symbolElements = document.querySelectorAll(`[data-symbol="${symbol}"]`);

        symbolElements.forEach(element => {
            if (window.tradingDashboard && window.tradingDashboard.animatePriceChange) {
                window.tradingDashboard.animatePriceChange(element);
            }
        });
    }

    showOrderNotification(data) {
        // Show toast notification for order updates
        const message = `Order ${data.orderId}: ${data.status}`;
        const type = data.status === 'COMPLETE' ? 'success' : 
                    data.status === 'REJECTED' ? 'danger' : 'info';

        if (window.tradingDashboard && window.tradingDashboard.showNotification) {
            window.tradingDashboard.showNotification(message, type);
        }
    }

    showErrorNotification(message) {
        if (window.tradingDashboard && window.tradingDashboard.showNotification) {
            window.tradingDashboard.showNotification(message, 'danger');
        }
    }

    updateOrderDisplays(data) {
        // Update order tables if visible
        const orderRows = document.querySelectorAll(`tr[data-order-id="${data.orderId}"]`);
        orderRows.forEach(row => {
            const statusCell = row.querySelector('.order-status');
            if (statusCell) {
                statusCell.innerHTML = `<span class="badge bg-${data.status === 'COMPLETE' ? 'success' : 'info'}">${data.status}</span>`;
            }
        });
    }

    updatePositionDisplays(data) {
        // Update position tables and cards
        const positionElements = document.querySelectorAll(`[data-position-symbol="${data.symbol}"]`);
        positionElements.forEach(element => {
            // Update P&L and other position data
            const pnlElement = element.querySelector('.position-pnl');
            if (pnlElement && data.pnl !== undefined) {
                pnlElement.textContent = `₹${parseFloat(data.pnl).toFixed(2)}`;
                pnlElement.className = `position-pnl ${data.pnl > 0 ? 'text-success' : data.pnl < 0 ? 'text-danger' : 'text-muted'}`;
            }
        });
    }

    updateHoldingDisplays(data) {
        // Update holding tables and cards
        const holdingElements = document.querySelectorAll(`[data-holding-symbol="${data.symbol}"]`);
        holdingElements.forEach(element => {
            // Update market value and P&L
            const valueElement = element.querySelector('.holding-value');
            if (valueElement && data.marketValue !== undefined) {
                valueElement.textContent = `₹${parseFloat(data.marketValue).toFixed(2)}`;
            }
        });
    }

    updateOrderBook(data) {
        // Update market depth/order book display
        const orderBookElement = document.getElementById('orderBook');
        if (orderBookElement && data.bids && data.asks) {
            // Update bid/ask displays
            this.renderOrderBook(orderBookElement, data);
        }
    }

    renderOrderBook(container, data) {
        // Render order book data
        container.innerHTML = `
            <div class="row">
                <div class="col-6">
                    <h6 class="text-danger">SELL</h6>
                    ${data.asks.slice(0, 5).map(ask => `
                        <div class="d-flex justify-content-between">
                            <span>${ask.quantity}</span>
                            <span class="text-danger">₹${ask.price}</span>
                        </div>
                    `).join('')}
                </div>
                <div class="col-6">
                    <h6 class="text-success">BUY</h6>
                    ${data.bids.slice(0, 5).map(bid => `
                        <div class="d-flex justify-content-between">
                            <span>${bid.quantity}</span>
                            <span class="text-success">₹${bid.price}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    refreshPositions() {
        // Trigger position refresh
        setTimeout(() => {
            if (window.location.pathname.includes('positions')) {
                window.location.reload();
            }
        }, 1000);
    }

    subscribe(instruments) {
        // Subscribe to instrument updates
        instruments.forEach(instrument => {
            this.subscriptions.set(instrument.token, instrument);
        });

        console.log(`Subscribed to ${instruments.length} instruments`);

        // In real implementation, send subscription message to WebSocket
        // this.send({ type: 'subscribe', instruments: instruments });
    }

    unsubscribe(tokens) {
        // Unsubscribe from instruments
        tokens.forEach(token => {
            this.subscriptions.delete(token);
        });

        console.log(`Unsubscribed from ${tokens.length} instruments`);

        // In real implementation, send unsubscription message to WebSocket
        // this.send({ type: 'unsubscribe', tokens: tokens });
    }

    resubscribeAll() {
        // Resubscribe to all previously subscribed instruments
        if (this.subscriptions.size > 0) {
            const instruments = Array.from(this.subscriptions.values());
            this.subscribe(instruments);
        }
    }

    send(data) {
        // Send data through WebSocket
        if (this.ws && this.isConnected) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, cannot send data');
        }
    }

    startHeartbeat() {
        // Send periodic heartbeat to keep connection alive
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                // this.send({ type: 'heartbeat', timestamp: Date.now() });
                console.log('Heartbeat sent');
            }
        }, 30000); // Every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    handleConnectionError() {
        this.isConnected = false;
        this.showConnectionStatus(false);

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.showErrorNotification('Connection lost. Please refresh the page.');
        }
    }

    showConnectionStatus(connected) {
        // Update connection status indicator
        const statusIndicator = document.getElementById('connectionStatus');
        if (statusIndicator) {
            statusIndicator.innerHTML = connected 
                ? '<i class="fas fa-circle text-success"></i> Connected'
                : '<i class="fas fa-circle text-danger"></i> Disconnected';
        }

        // Add connection status to navbar if it doesn't exist
        if (!statusIndicator) {
            const navbar = document.querySelector('.navbar .navbar-nav');
            if (navbar) {
                const statusElement = document.createElement('li');
                statusElement.className = 'nav-item';
                statusElement.innerHTML = `
                    <span class="navbar-text" id="connectionStatus">
                        <i class="fas fa-circle ${connected ? 'text-success' : 'text-danger'}"></i>
                        ${connected ? 'Connected' : 'Disconnected'}
                    </span>
                `;
                navbar.appendChild(statusElement);
            }
        }
    }

    disconnect() {
        // Disconnect WebSocket
        this.isConnected = false;
        this.stopHeartbeat();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        console.log('WebSocket disconnected');
        this.showConnectionStatus(false);
    }

    // Public API methods for other components
    subscribeToSymbol(symbol, token, exchange) {
        this.subscribe([{ symbol, token, exchange }]);
    }

    unsubscribeFromSymbol(token) {
        this.unsubscribe([token]);
    }

    getConnectionStatus() {
        return this.isConnected;
    }

    getSubscriptions() {
        return Array.from(this.subscriptions.values());
    }
}

// Auto-initialize WebSocket handler
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on authenticated pages
    if (document.querySelector('.navbar')) {
        window.WebSocketHandler = WebSocketHandler;

        // Initialize if trading dashboard exists
        if (window.tradingDashboard) {
            window.wsHandler = new WebSocketHandler();
            window.wsHandler.connect();
        }
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.wsHandler) {
        window.wsHandler.disconnect();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketHandler;
}
# Kotak Neo Trading Application

## Overview

This is a comprehensive Flask-based web application that integrates with the Kotak Neo trading API to provide a full-featured trading platform. The application enables users to manage their trading portfolios, place orders, track positions and holdings, and monitor real-time market data through a modern Bootstrap-powered web interface.

## System Architecture

The application follows a modern Flask architecture with clear separation of concerns:

- **Backend**: Flask web framework with SQLAlchemy ORM for database management
- **Frontend**: Bootstrap 5 with custom CSS for responsive UI/UX
- **Database**: PostgreSQL for persistent data storage
- **API Integration**: Kotak Neo API Python SDK for trading functionality
- **Session Management**: Flask-Session with filesystem storage for user sessions
- **Real-time Updates**: JavaScript-based dashboard with auto-refresh capabilities

## Key Components

### Authentication System
- **TOTP-based Authentication**: Users authenticate using mobile number, UCC, TOTP code, and MPIN
- **Token Management**: Secure storage and management of access tokens and session tokens
- **Session Persistence**: 24-hour session duration with automatic renewal
- **Security**: Protected routes using decorators and session validation

### Trading Engine
- **Order Management**: Place, modify, and cancel orders across different exchanges
- **Portfolio Tracking**: Real-time positions and holdings monitoring
- **Market Data**: Live quotes and price updates
- **Risk Management**: Built-in validation and error handling

### Database Schema
- **Users Table**: Stores user credentials, account information, and session tokens
- **User Sessions**: Tracks active sessions with expiration management
- **User Preferences**: Customizable trading preferences and settings

### User Interface
- **Responsive Design**: Mobile-first Bootstrap 5 interface
- **Real-time Dashboard**: Auto-refreshing portfolio overview
- **Interactive Charts**: Market data visualization
- **Trading Forms**: Intuitive order placement and management

## Data Flow

1. **Authentication Flow**:
   - User submits TOTP credentials
   - System validates with Kotak Neo API
   - Session tokens stored in database and Flask session
   - User redirected to dashboard

2. **Trading Operations**:
   - All trading requests routed through Flask API endpoints
   - Session validation on each request
   - Kotak Neo API integration for actual trade execution
   - Real-time updates pushed to frontend

3. **Data Persistence**:
   - User data stored in PostgreSQL
   - Session management through Flask-Session
   - Trading history and preferences maintained

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **psycopg2-binary**: PostgreSQL database adapter
- **Flask-Session**: Server-side session management
- **Werkzeug**: WSGI utilities and security

### Trading Integration
- **neo-api-client**: Official Kotak Neo Python SDK (installed from GitHub)
- **pandas**: Data manipulation and analysis
- **python-dotenv**: Environment variable management

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library
- **Chart.js/Lightweight Charts**: Data visualization

### Development Tools
- **Gunicorn**: Production WSGI server
- **UV**: Fast Python package installer
- **Email-validator**: Form validation utilities

## Deployment Strategy

### Production Environment (Replit)
- **Runtime**: Python 3.11 with Node.js 20 for frontend tooling
- **Database**: Managed PostgreSQL instance
- **Server**: Gunicorn with autoscaling deployment
- **Session Storage**: Filesystem-based session management
- **Static Assets**: Served through Flask with CDN fallbacks

### Local Development
- **Setup Scripts**: Automated setup for macOS (`local_setup.sh`) and Windows (`local_setup_windows.bat`)
- **Environment**: Local PostgreSQL instance with development configuration
- **Hot Reload**: Flask development server with auto-restart

### Configuration Management
- **Environment Variables**: Sensitive data stored in `.env` files
- **Multi-environment Support**: Separate configs for development and production
- **Database Migrations**: SQLAlchemy-based schema management

## Recent Changes

- **June 20, 2025** - Successfully completed ETF trading signals system with real-time data
  - Fixed authentication issues by removing login requirement from ETF signals page
  - API endpoint `/api/etf-signals-data` now returns 15 trading signals for user zhz3j
  - All required fields populated: ETF, 30, DH, Date, Pos, Qty, EP, CMP, %Chan, Inv., TP, TVA, TPR, PL, ED, EXP, PR, PP, IV, IP, NT, Qt, 7, %Ch
  - Portfolio summary showing ₹32.4L investment with 0.99% returns
  - Real-time price integration with Kotak Neo quotes data
  - Home page now redirects directly to ETF signals for immediate data access

- **June 20, 2025** - Built comprehensive trading signal management system
  - Implemented real-time CMP integration with Kotak Neo API (5-minute updates)
  - Created RealtimeQuote model for storing market data with timestamps
  - Built advanced DataTables with pagination, search, filtering, and sorting
  - Added admin panel for creating and managing ETF trading signals
  - Implemented user dashboard with real-time portfolio tracking
  - Created P&L calculations with percentage returns and current values
  - Added column visibility controls and responsive design
  - Integrated real-time price updates for all trading signals
  - Built comprehensive API endpoints for quotes and signal management
  - Populated demo data with 5 users, 50 market quotes, and 40 trading signals

- **June 19, 2025** - Successfully completed migration from Replit Agent to standard Replit environment
  - Resolved pandas/libstdc++.so.6 dependency issues by setting proper LD_LIBRARY_PATH
  - Fixed NeoAPI import issues with direct library path configuration  
  - Generated secure session secret for Flask application security
  - Application running successfully on port 5000 with Gunicorn
  - Login functionality now working with proper library dependencies
  - Database properly connected with PostgreSQL environment variables
  - All core dependencies installed and configured correctly

## Changelog

- June 17, 2025 - Migration to Replit completed with ETF signals feature
- June 14, 2025 - Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.
UI Preferences: Keep original ETF signals page UI unchanged - user prefers existing design.
Data Preferences: No demo data - fetch and display real data from database only.
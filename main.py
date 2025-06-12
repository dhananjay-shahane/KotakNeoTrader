from flask import Flask, render_template, send_from_directory
from flask_session import Session
from flask import Blueprint

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this!

Session(app)

# Define blueprints
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
trading_api = Blueprint('trading_api', __name__)


# Example route for main blueprint
@main_bp.route('/')
def index():
    return "Hello, world!"

# Example route for auth blueprint
@auth_bp.route('/login')
def login():
    return "Login page"

# Example route for trading api
@trading_api.route('/stocks')
def stocks():
    return "List of Stocks"

# Import and register dashboard API
dashboard_api = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')

@dashboard_api.route('/user_profile')
def user_profile():
    return jsonify({"username": "example_user", "email": "user@example.com"})

@dashboard_api.route('/portfolio_summary')
def portfolio_summary():
    return jsonify({"total_value": 100000, "cash": 20000})

@dashboard_api.route('/positions')
def positions():
    return jsonify([{"symbol": "AAPL", "quantity": 10}, {"symbol": "GOOG", "quantity": 5}])

@dashboard_api.route('/live_quotes')
def live_quotes():
    return jsonify({"AAPL": 150.25, "GOOG": 2700.50})

from flask import jsonify
# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(trading_api)
app.register_blueprint(dashboard_api, url_prefix='/api/dashboard')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
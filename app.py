import datetime, jwt, os
from functools import wraps
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)

# Configure database URI and secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/portfolio_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    portfolios = db.relationship('Portfolio', backref='owner', lazy=True)

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    transactions = db.relationship('Transaction', backref='portfolio', lazy=True)

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100))
    asset_type = db.Column(db.String(20))
    transactions = db.relationship('Transaction', backref='asset', lazy=True)
    quotes = db.relationship('Quote', backref='asset', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    quantity = db.Column(db.Numeric(20,4), nullable=False)
    price = db.Column(db.Numeric(20,4), nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Quote(db.Model):
    __tablename__ = 'quotes'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    quote_date = db.Column(db.Date, nullable=False)
    open = db.Column(db.Numeric(20,4))
    close = db.Column(db.Numeric(20,4))
    high = db.Column(db.Numeric(20,4))
    low = db.Column(db.Numeric(20,4))
    volume = db.Column(db.BigInteger)
    __table_args__ = (db.UniqueConstraint('asset_id', 'quote_date', name='unique_asset_date'),)

# JWT utility functions
def encode_auth_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    except Exception as e:
        return None

def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers.get('Authorization').split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        user_id = decode_auth_token(token)
        if not user_id:
            return jsonify({'message': 'Token is invalid or expired!'}), 401
        return f(user_id, *args, **kwargs)
    return decorated

# API Endpoints

# User Registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'message': 'User already exists'}), 400
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

# User Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials'}), 401
    token = encode_auth_token(user.id)
    return jsonify({'token': token}), 200

# Portfolio Management
@app.route('/api/portfolios', methods=['GET', 'POST'])
@token_required
def portfolios(current_user_id):
    if request.method == 'GET':
        portfolios = Portfolio.query.filter_by(user_id=current_user_id).all()
        return jsonify([{'id': p.id, 'name': p.name, 'created_at': p.created_at.isoformat()} for p in portfolios])
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        new_portfolio = Portfolio(user_id=current_user_id, name=name)
        db.session.add(new_portfolio)
        db.session.commit()
        return jsonify({'message': 'Portfolio created', 'id': new_portfolio.id}), 201

# Adding Transactions
@app.route('/api/transactions', methods=['POST'])
@token_required
def add_transaction(current_user_id):
    data = request.json
    portfolio_id = data.get('portfolio_id')
    asset_ticker = data.get('asset_ticker')
    transaction_type = data.get('transaction_type')  # 'buy' or 'sell'
    quantity = data.get('quantity')
    price = data.get('price')
    
    # Validate portfolio ownership
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user_id).first()
    if not portfolio:
        return jsonify({'message': 'Portfolio not found'}), 404
    
    # Find or create asset
    asset = Asset.query.filter_by(ticker=asset_ticker).first()
    if not asset:
        asset = Asset(ticker=asset_ticker, name=asset_ticker, asset_type='stock')
        db.session.add(asset)
        db.session.commit()
    
    transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        transaction_type=transaction_type,
        quantity=quantity,
        price=price
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'message': 'Transaction added'}), 201

# Portfolio Summary (Aggregated Data)
@app.route('/api/portfolio/<int:portfolio_id>', methods=['GET'])
@token_required
def portfolio_summary(current_user_id, portfolio_id):
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user_id).first()
    if not portfolio:
        return jsonify({'message': 'Portfolio not found'}), 404
    
    transactions = Transaction.query.filter_by(portfolio_id=portfolio_id).all()
    summary = {}
    for tx in transactions:
        asset = Asset.query.get(tx.asset_id)
        if asset.ticker not in summary:
            summary[asset.ticker] = {'quantity': 0, 'total_invested': 0}
        if tx.transaction_type == 'buy':
            summary[asset.ticker]['quantity'] += float(tx.quantity)
            summary[asset.ticker]['total_invested'] += float(tx.quantity) * float(tx.price)
        else:  # sell
            summary[asset.ticker]['quantity'] -= float(tx.quantity)
            summary[asset.ticker]['total_invested'] -= float(tx.quantity) * float(tx.price)
    return jsonify({'portfolio': portfolio.name, 'summary': summary})

# Dummy Quote Endpoint (In a real app, integrate with a financial API)
@app.route('/api/quotes/<string:ticker>', methods=['GET'])
def get_quote(ticker):
    asset = Asset.query.filter_by(ticker=ticker).first()
    if not asset:
        return jsonify({'message': 'Asset not found'}), 404
    # Return dummy data if no quote available
    quote = Quote.query.filter_by(asset_id=asset.id).order_by(Quote.quote_date.desc()).first()
    if not quote:
        return jsonify({
            'ticker': ticker,
            'quote_date': str(datetime.date.today()),
            'open': 100,
            'close': 105,
            'high': 110,
            'low': 95,
            'volume': 1000000
        })
    return jsonify({
        'ticker': ticker,
        'quote_date': str(quote.quote_date),
        'open': float(quote.open),
        'close': float(quote.close),
        'high': float(quote.high),
        'low': float(quote.low),
        'volume': quote.volume
    })

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, port=5000)

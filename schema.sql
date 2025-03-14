-- Users table: Stores user information.
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Portfolios table: Each user can have one or more portfolios.
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assets table: Represents financial instruments (e.g., stocks).
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100),
    asset_type VARCHAR(20)
);

-- Transactions table: Records buy/sell transactions in a portfolio.
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    transaction_type VARCHAR(10) CHECK (transaction_type IN ('buy', 'sell')),
    quantity NUMERIC(20,4) NOT NULL,
    price NUMERIC(20,4) NOT NULL,
    transaction_date TIMESTAMP DEFAULT NOW()
);

-- Quotes table: Historical price data for assets.
CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    quote_date DATE NOT NULL,
    open NUMERIC(20,4),
    close NUMERIC(20,4),
    high NUMERIC(20,4),
    low NUMERIC(20,4),
    volume BIGINT,
    UNIQUE(asset_id, quote_date)
);

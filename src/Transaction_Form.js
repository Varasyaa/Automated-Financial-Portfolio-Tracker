// src/TransactionForm.js
import React, { useState } from 'react';
import axios from 'axios';

function TransactionForm({ portfolioId }) {
  const [assetTicker, setAssetTicker] = useState('');
  const [transactionType, setTransactionType] = useState('buy');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const token = localStorage.getItem('token');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:5000/api/transactions', {
        portfolio_id: portfolioId,
        asset_ticker: assetTicker,
        transaction_type: transactionType,
        quantity: quantity,
        price: price
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      alert('Transaction added');
      setAssetTicker('');
      setQuantity('');
      setPrice('');
    } catch (error) {
      console.error(error);
      alert('Error adding transaction');
    }
  };

  return (
    <div>
      <h3>Add Transaction</h3>
      <form onSubmit={handleSubmit}>
        <input type="text" placeholder="Asset Ticker" value={assetTicker} onChange={e => setAssetTicker(e.target.value)} required />
        <select value={transactionType} onChange={e => setTransactionType(e.target.value)}>
          <option value="buy">Buy</option>
          <option value="sell">Sell</option>
        </select>
        <input type="number" step="0.0001" placeholder="Quantity" value={quantity} onChange={e => setQuantity(e.target.value)} required />
        <input type="number" step="0.0001" placeholder="Price" value={price} onChange={e => setPrice(e.target.value)} required />
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}

export default TransactionForm;

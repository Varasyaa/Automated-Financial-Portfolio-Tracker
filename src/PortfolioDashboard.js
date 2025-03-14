// src/PortfolioDashboard.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import TransactionForm from './TransactionForm';
import { Line } from 'react-chartjs-2';

function PortfolioDashboard() {
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [summary, setSummary] = useState({});
  const token = localStorage.getItem('token');

  useEffect(() => {
    axios.get('http://localhost:5000/api/portfolios', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(res => {
      setPortfolios(res.data);
      if (res.data.length > 0) {
        setSelectedPortfolio(res.data[0].id);
      }
    }).catch(err => console.error(err));
  }, [token]);

  useEffect(() => {
    if (selectedPortfolio) {
      axios.get(`http://localhost:5000/api/portfolio/${selectedPortfolio}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(res => {
        setSummary(res.data.summary);
      }).catch(err => console.error(err));
    }
  }, [selectedPortfolio, token]);

  const chartData = {
    labels: Object.keys(summary),
    datasets: [
      {
        label: 'Quantity',
        data: Object.values(summary).map(item => item.quantity),
        backgroundColor: 'rgba(75,192,192,0.4)'
      },
      {
        label: 'Total Invested',
        data: Object.values(summary).map(item => item.total_invested),
        backgroundColor: 'rgba(255,99,132,0.4)'
      }
    ]
  };

  return (
    <div>
      <h2>Portfolio Dashboard</h2>
      <div>
        <label>Select Portfolio: </label>
        <select onChange={(e) => setSelectedPortfolio(e.target.value)} value={selectedPortfolio}>
          {portfolios.map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>
      <div>
        <h3>Summary</h3>
        <Line data={chartData} />
      </div>
      <TransactionForm portfolioId={selectedPortfolio} />
    </div>
  );
}

export default PortfolioDashboard;

import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const Dashboard = () => {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Backend configuration
  const BACKEND_URL = 'http://localhost:5001';
  const API_URL = `${BACKEND_URL}/api/nodes`;

  // Fetch nodes via REST API
  const fetchNodes = async () => {
    try {
      const response = await fetch(API_URL);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setNodes(data.nodes);
        setLastUpdate(new Date());
        setError(null);
      } else {
        throw new Error(data.error || 'Failed to fetch nodes');
      }
    } catch (err) {
      console.error('Error fetching nodes:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch on mount and every 5 seconds
  useEffect(() => {
    fetchNodes(); // Initial fetch
    
    const interval = setInterval(() => {
      fetchNodes();
    }, 5000); // Refresh every 5 seconds
    
    return () => clearInterval(interval);
  }, []);

  // Calculate time since last seen
  const getTimeSince = (timestamp) => {
    if (!timestamp) return 'Never';
    
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffSec = Math.floor(diffMs / 1000);
    
    if (diffSec < 10) return 'Just now';
    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return `${Math.floor(diffSec / 86400)}d ago`;
  };

  // Determine node status based on last seen
  const getNodeStatus = (lastSeen) => {
    if (!lastSeen) return 'offline';
    
    const now = new Date();
    const then = new Date(lastSeen);
    const diffSec = (now - then) / 1000;
    
    if (diffSec < 300) return 'online';      // Less than 15 seconds
    if (diffSec < 600) return 'warning';    // Less than 2 minutes
    return 'offline';
  };

  // Count nodes by status
  const getStatusCounts = () => {
    const counts = { online: 0, warning: 0, offline: 0 };
    nodes.forEach(node => {
      const status = getNodeStatus(node.last_seen);
      counts[status]++;
    });
    return counts;
  };

  const statusCounts = getStatusCounts();

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1> Group 8: Garbage Monitoring Sensor Demostration</h1>
        </div>
        
        <div className="header-info">
          <div className="status-summary">
            <span className="status-count online">
              <span className="status-dot"></span>
              {statusCounts.online} Online
            </span>
            <span className="status-count warning">
              <span className="status-dot"></span>
              {statusCounts.warning} Idle
            </span>
            <span className="status-count offline">
              <span className="status-dot"></span>
              {statusCounts.offline} Offline
            </span>
          </div>
          
          <div className="header-meta">
            <span className="node-count">
              {nodes.length} Node{nodes.length !== 1 ? 's' : ''} Total
            </span>
            {lastUpdate && (
              <span className="last-update">
                Updated: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </div>
          
          <button onClick={fetchNodes} className="refresh-btn" disabled={loading}>
            {loading ? '⟳' : '🔄'} Refresh
          </button>
        </div>
      </header>

      {loading && nodes.length === 0 && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading sensor network...</p>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={fetchNodes}>Retry</button>
        </div>
      )}

      {!loading && nodes.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-icon">📡</div>
          <h2>No Nodes Registered</h2>
          <p>Your ESP32 sensor network is empty.</p>
          <div className="empty-instructions">
            <h3>To add a node:</h3>
            <ol>
              <li>Get the last 4 digits of your ESP32's chip ID from Serial Monitor</li>
              <li>Register the node using the API or admin panel</li>
              <li>Power on your ESP32 and wait for data</li>
            </ol>
          </div>
          <div className="api-example">
            <h4>Example API Call:</h4>
            <code>
              curl -X POST {API_URL} \<br/>
              &nbsp;&nbsp;-H "Content-Type: application/json" \<br/>
              &nbsp;&nbsp;-d '{`{"name": "Sensor 1", "chip_id": "5788"}`}'
            </code>
          </div>
        </div>
      )}

      <div className="nodes-grid">
        {nodes.map((node) => {
          const status = getNodeStatus(node.last_seen);
          
          return (
            <div key={node.id} className={`node-card ${status}`}>
              <div className="node-header">
                <div className="node-title">
                  <h3>{node.name}</h3>
                  <span className="chip-id">Chip: {node.chip_id}</span>
                </div>
                <div className={`status-indicator ${status}`}>
                  <span className="status-dot"></span>
                  <span className="status-text">
                    {status === 'online' && 'Online'}
                    {status === 'warning' && 'Idle'}
                    {status === 'offline' && 'Offline'}
                  </span>
                </div>
              </div>

              <div className="node-data">
                <div className="data-row highlight">
                  <span className="data-label">
                    <span className="data-icon">📏</span>
                    Distance
                  </span>
                  <span className="data-value">
                    {node.latest_cm !== null && node.latest_cm !== undefined 
                      ? `${node.latest_cm} cm` 
                      : 'No data'}
                  </span>
                </div>
                
                <div className="data-row">
                  <span className="data-label">
                    <span className="data-icon">📐</span>
                    Imperial
                  </span>
                  <span className="data-value secondary">
                    {node.latest_inches !== null && node.latest_inches !== undefined 
                      ? `${node.latest_inches} in` 
                      : 'No data'}
                  </span>
                </div>

                <div className="data-row">
                  <span className="data-label">
                    <span className="data-icon">🔄</span>
                    Boot Count
                  </span>
                  <span className="data-value secondary">
                    {node.boot_count !== null && node.boot_count !== undefined 
                      ? node.boot_count 
                      : 'N/A'}
                  </span>
                </div>

                <div className="data-row">
                  <span className="data-label">
                    <span className="data-icon">📊</span>
                    Total Readings
                  </span>
                  <span className="data-value secondary">
                    {node.reading_count || 0}
                  </span>
                </div>

                <div className="data-row">
                  <span className="data-label">
                    <span className="data-icon">⏱️</span>
                    Last Seen
                  </span>
                  <span className="data-value secondary">
                    {getTimeSince(node.last_seen)}
                  </span>
                </div>
              </div>

              <div className="node-footer">
                <small className="timestamp">
                  {node.last_seen 
                    ? `Last update: ${new Date(node.last_seen).toLocaleString()}`
                    : 'Waiting for first reading...'}
                </small>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Dashboard;
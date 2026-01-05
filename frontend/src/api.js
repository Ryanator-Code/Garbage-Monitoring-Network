// API service layer for sensor network dashboard
// Backend: 10.0.0.234:5001

const API_BASE_URL = 'http://10.0.0.234:5001';

/**
 * GET /dashboard
 * List all nodes in the network
 * 
 * Returns: [{ name, distance, battery, role, chip_id }, ...]
 */
export const getAllNodes = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard`);
    if (!response.ok) throw new Error('Failed to fetch nodes');
    const data = await response.json();
    // Convert backend format to frontend format
    // Backend returns: { name, distance, battery, role, chip_id, last_update, uptime_ms, last_cycle_uptime_ms, uptime_status }
    // Frontend expects: { chipId, name, distance, battery, role, lastUpdate, uptimeMs, lastCycleUptimeMs, uptimeStatus }
    return data.map(node => ({
      chipId: node.chip_id || node.chipId, // Support both formats
      name: node.name,
      distance: node.distance,
      battery: node.battery,
      role: node.role,
      lastUpdate: node.last_update,
      uptimeMs: node.uptime_ms,
      lastCycleUptimeMs: node.last_cycle_uptime_ms,
      uptimeStatus: node.uptime_status
    }));
  } catch (error) {
    console.error('Error fetching nodes:', error);
    // Return empty array on error (no mock data)
    return [];
  }
};

/**
 * GET /api/status
 * Get system-level statistics (including average cycle uptime)
 */
export const getSystemStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/status`);
    if (!response.ok) throw new Error('Failed to fetch system status');
    const data = await response.json();
    return {
      totalNodes: data.total_nodes,
      activeNodes: data.active_nodes,
      avgCycleUptimeMs: data.avg_cycle_uptime_ms ?? null,
    };
  } catch (error) {
    console.error('Error fetching system status:', error);
    return null;
  }
};

/**
 * GET /dashboard/:chip_id
 * Get history for a specific node
 * 
 * Returns: [{ timestamp, distance, battery }, ...]
 */
export const getNodeData = async (chipId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard/${chipId}`);
    if (!response.ok) throw new Error('Failed to fetch node data');
    const data = await response.json();
    // Expected format: [{ timestamp, distance, battery }]
    return data;
  } catch (error) {
    console.error('Error fetching node data:', error);
    // Return empty array on error
    return [];
  }
};

/**
 * POST /dashboard/:chip_id
 * Update node name
 * 
 * Body: { name: "New Name" }
 */
export const updateNodeName = async (chipId, name) => {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard/${chipId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) throw new Error('Failed to update node name');
    const data = await response.json();
    return {
      success: data.success,
      chipId: data.chip_id || chipId,
      name: data.name
    };
  } catch (error) {
    console.error('Error updating node name:', error);
    return { success: false, error: error.message };
  }
};

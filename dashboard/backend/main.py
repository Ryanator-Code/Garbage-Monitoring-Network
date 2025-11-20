"""
ESP32 Sensor Network - Flask Application

Main Flask application with REST API endpoints for:
- Node management (add, delete, list)
- ESP32 data reception
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from storage import storage
from ESP import esp_receiver

# =====================================================
# FLASK APP SETUP
# =====================================================

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# =====================================================
# NODE MANAGEMENT ENDPOINTS
# =====================================================

@app.route('/api/nodes', methods=['GET'])
def get_all_nodes():
    """
    Get all nodes (for dashboard)
    Returns summary data without history
    """
    nodes_list = storage.get_all_nodes_summary()
    return jsonify({
        "success": True,
        "count": len(nodes_list),
        "nodes": nodes_list
    })


@app.route('/api/nodes', methods=['POST'])
def add_node():
    """
    Add a new node to the network
    
    Required body:
    {
        "name": "Node Name",
        "chip_id": "A3B7"  // Last 4 digits of ESP32 chip ID
    }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    if 'name' not in data:
        return jsonify({
            "success": False,
            "error": "Node name is required"
        }), 400
    
    if 'chip_id' not in data:
        return jsonify({
            "success": False,
            "error": "Chip ID is required"
        }), 400
    
    name = data['name'].strip()
    chip_id = data['chip_id'].strip()
    
    # Validate name
    if not name:
        return jsonify({
            "success": False,
            "error": "Node name cannot be empty"
        }), 400
    
    # Validate chip_id format
    if len(chip_id) != 4:
        return jsonify({
            "success": False,
            "error": "Chip ID must be exactly 4 characters"
        }), 400
    
    # Check if chip_id is already registered
    availability = esp_receiver.validate_chip_id_available(chip_id)
    if not availability["available"]:
        return jsonify({
            "success": False,
            "error": availability["message"]
        }), 409  # Conflict
    
    # Create the node
    node_id = storage.create_node(name, chip_id)
    node = storage.get_node_summary(node_id)
    
    print(f"[Node Added] {name} (Chip ID: {chip_id.upper()}) -> Node ID: {node_id}")
    
    return jsonify({
        "success": True,
        "message": "Node added successfully",
        "node": node
    }), 201


@app.route('/api/nodes/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    """Delete a node from the network"""
    
    # Check if node exists
    if not storage.node_exists(node_id):
        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404
    
    # Get node info before deletion
    node = storage.get_node_summary(node_id)
    node_name = node["name"]
    
    # Delete the node
    storage.delete_node(node_id)
    
    print(f"[Node Deleted] {node_name} (ID: {node_id})")
    
    return jsonify({
        "success": True,
        "message": f"Node '{node_name}' deleted successfully"
    })


@app.route('/api/nodes/<node_id>', methods=['GET'])
def get_node_detail(node_id):
    """
    Get full node details including history
    For the detail page
    """
    node = storage.get_node_full(node_id)
    
    if not node:
        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404
    
    # Add statistics
    stats = storage.get_node_statistics(node_id)
    node["statistics"] = stats
    
    return jsonify({
        "success": True,
        "node": node
    })


# =====================================================
# ESP32 DATA ENDPOINT
# =====================================================

@app.route('/api/data', methods=['POST'])
def receive_esp_data():
    """
    Receive sensor data from ESP32
    
    Required body:
    {
        "chip_id": "A3B7",
        "cm": 45.5,
        "inches": 17.9,
        "boot": 1
    }
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['chip_id', 'cm', 'inches', 'boot']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            "success": False,
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Extract data
    chip_id = data['chip_id']
    cm = data['cm']
    inches = data['inches']
    boot_count = data['boot']
    
    # Process through ESP receiver
    result = esp_receiver.receive_data(chip_id, cm, inches, boot_count)
    
    if not result["success"]:
        # Determine appropriate status code
        status_code = 404 if result.get("error") == "NODE_NOT_REGISTERED" else 400
        return jsonify(result), status_code
    
    return jsonify(result)


# =====================================================
# UTILITY ENDPOINTS
# =====================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get server status and statistics"""
    return jsonify({
        "success": True,
        "status": "running",
        "total_nodes": storage.get_node_count(),
        "active_nodes": storage.get_active_node_count(),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/validate-chip-id/<chip_id>', methods=['GET'])
def validate_chip_id(chip_id):
    """Check if a chip ID is available"""
    result = esp_receiver.validate_chip_id_available(chip_id)
    return jsonify(result)


@app.route('/', methods=['GET'])
def index():
    """API information endpoint"""
    return jsonify({
        "name": "ESP32 Sensor Network API",
        "version": "1.0",
        "endpoints": {
            "GET /api/nodes": "Get all nodes (dashboard)",
            "POST /api/nodes": "Add new node (body: {name, chip_id})",
            "DELETE /api/nodes/<id>": "Delete a node",
            "GET /api/nodes/<id>": "Get node details with history",
            "POST /api/data": "Receive sensor data from ESP32 (body: {chip_id, cm, inches, boot})",
            "GET /api/validate-chip-id/<id>": "Check if chip ID is available",
            "GET /api/status": "Get server status"
        }
    })


# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':
    print("=" * 70)
    print(" ESP32 SENSOR NETWORK - Backend Server")
    print("=" * 70)
    print("\n🚀 Server Configuration:")
    print(f"   Host: 0.0.0.0")
    print(f"   Port: 5001")
    print(f"   URL:  http://localhost:5001")
    print("\n📡 API Endpoints:")
    print("   GET    /api/nodes              - List all nodes")
    print("   POST   /api/nodes              - Add new node")
    print("   DELETE /api/nodes/<id>         - Delete node")
    print("   GET    /api/nodes/<id>         - Get node details")
    print("   POST   /api/data               - Receive ESP32 data")
    print("   GET    /api/validate-chip-id/<id> - Check chip ID")
    print("   GET    /api/status             - Server status")
    print("\n💡 Usage:")
    print("   1. Add nodes via POST /api/nodes with name and chip_id")
    print("   2. Configure ESP32 with chip_id (last 4 digits of chip ID)")
    print("   3. ESP32 sends data to POST /api/data")
    print("   4. Dashboard polls /api/nodes every 5 seconds for updates")
    print("\n📊 Dashboard Updates:")
    print("   Frontend polls every 5 seconds (no WebSocket needed)")
    print("\n" + "=" * 70)
    print("Starting server...\n")
    
    # Run normal Flask app (no socketio)
    app.run(host='0.0.0.0', port=5001, debug=True)
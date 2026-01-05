

import os
import csv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from storage import storage
from esp import esp_receiver
from battery_logger import LOG_PATH as BATTERY_LOG_PATH

app = Flask(__name__)
CORS(app) 

@app.route('/dashboard', methods=['GET'])
def get_dashboard():

    nodes_list = storage.get_all_dashboard_summary()
    return jsonify(nodes_list)


@app.route('/dashboard/<chip_id>', methods=['GET'])
def get_node_history(chip_id):

    history = storage.get_node_history(chip_id)
    
    if history is None:
        return jsonify({
            "error": "Node not found"
        }), 404
    
    return jsonify(history)


@app.route('/dashboard/<chip_id>', methods=['POST'])
def set_node_name(chip_id):
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    if 'name' not in data:
        return jsonify({
            "success": False,
            "error": "Name field is required"
        }), 400
    
    if not storage.node_exists(chip_id):
        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404
    
    name = data['name']
    
    storage.update_node_name(chip_id, name)
    
    display_name = storage.get_display_name(chip_id)
    
    print(f"[Node Renamed] {chip_id} -> '{display_name}'")
    
    return jsonify({
        "success": True,
        "message": "Node name updated",
        "chip_id": chip_id.upper(),
        "name": display_name
    })


@app.route('/api/data', methods=['POST'])
def receive_esp_data():
    data = request.get_json()
    
    if data is None:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    result = esp_receiver.receive_batch_data(data)
    
    if not result["success"]:
        return jsonify(result), 400
    
    return jsonify(result)



@app.route('/api/status', methods=['GET'])
def get_status():
    """Get server status and statistics"""
    avg_cycle_uptime_ms = storage.get_average_cycle_uptime_ms()
    return jsonify({
        "success": True,
        "status": "running",
        "total_nodes": storage.get_node_count(),
        "active_nodes": storage.get_active_node_count(),
        "avg_cycle_uptime_ms": avg_cycle_uptime_ms,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/nodes/<chip_id>', methods=['DELETE'])
def delete_node(chip_id):
    
    if not storage.node_exists(chip_id):
        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404
    
    display_name = storage.get_display_name(chip_id)
    
    storage.delete_node(chip_id)
    
    print(f"[Node Deleted] {display_name} (Chip ID: {chip_id})")
    
    return jsonify({
        "success": True,
        "message": f"Node '{display_name}' deleted successfully"
    })


@app.route('/api/nodes/<chip_id>', methods=['GET'])
def get_node_detail(chip_id):
  
    node = storage.get_node_full(chip_id)
    
    if not node:
        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404
    
    stats = storage.get_node_statistics(chip_id)
    node["statistics"] = stats
    
    return jsonify({
        "success": True,
        "node": node
    })


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "ESP32 Garbage Sensor Network API",
        "version": "2.0",
        "endpoints": {
            "GET /dashboard": "Get all nodes for dashboard (name defaults to chip_id if unnamed)",
            "GET /dashboard/<chip_id>": "Get node history",
            "POST /dashboard/<chip_id>": "Set node name (body: {name})",
            "POST /api/data": "Receive ESP32 batch data (body: [{node_mac, distance, uptime_ms, battery, role, chipId}, ...])",
            "GET /api/status": "Get server status",
            "GET /api/nodes/<chip_id>": "Get full node details",
            "DELETE /api/nodes/<chip_id>": "Delete a node"
        }
    })

@app.route('/api/battery-log', methods=['GET'])
def get_battery_log():
    entries = []
    if os.path.exists(BATTERY_LOG_PATH):
        try:
            with open(BATTERY_LOG_PATH, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    def to_float(value):
                        return float(value) if value not in (None, "",) else None

                    def to_int(value):
                        return int(value) if value not in (None, "",) else None

                    entries.append({
                        "timestamp": row.get("timestamp"),
                        "chip_id": row.get("chip_id"),
                        "node_mac": row.get("node_mac"),
                        "role": row.get("role"),
                        "battery": to_float(row.get("battery")),
                        "distance": to_float(row.get("distance")),
                        "uptime_ms": to_int(row.get("uptime_ms")),
                    })
        except Exception as exc:
            return jsonify({
                "success": False,
                "error": f"Failed to read battery log: {exc}"
            }), 500

    return jsonify(entries)


@app.route('/battery-viewer', methods=['GET'])
def battery_viewer_page():
    
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    return send_from_directory(static_dir, "battery_viewer.html")




if __name__ == '__main__':
    print("Starting server...\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)

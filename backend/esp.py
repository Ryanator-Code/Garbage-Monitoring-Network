

from storage import storage
from datetime import datetime


class ESPDataReceiver:
    
    def __init__(self):
        pass
    
    
    def receive_batch_data(self, nodes_data):

        if not nodes_data or not isinstance(nodes_data, list):
            return {
                "success": False,
                "message": "Invalid data format. Expected array of node data.",
                "error": "INVALID_FORMAT"
            }
        
        processed = 0
        errors = []
        
        for node_data in nodes_data:
            result = self._process_single_node(node_data)
            if result["success"]:
                processed += 1
            else:
                errors.append({
                    "chip_id": node_data.get("chipId", "unknown"),
                    "error": result["message"]
                })
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Batch received: {processed}/{len(nodes_data)} nodes processed")
        
        return {
            "success": True,
            "message": f"Processed {processed} of {len(nodes_data)} nodes",
            "processed": processed,
            "total": len(nodes_data),
            "errors": errors if errors else None
        }
    
    
    def _process_single_node(self, node_data):
        print(f"[DEBUG] Received node data: {node_data}")
        required_fields = ['distance', 'battery']
        missing_fields = [f for f in required_fields if f not in node_data]
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            print(f"[ERROR] {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }
        
        node_mac = node_data.get('node_mac', '')
        if node_mac and isinstance(node_mac, str):
            octets = node_mac.split(':')
            if len(octets) >= 2:
                chip_id = (octets[-2] + octets[-1]).upper()
            else:
                chip_id = node_data.get('chipId') or node_data.get('chip_id')
        else:
            chip_id = node_data.get('chipId') or node_data.get('chip_id')
        
        if isinstance(chip_id, int):
            chip_id = format(chip_id & 0xFFFFFFFF, '08X')[-4:]  # Last 4 hex chars
        
        if not chip_id or not isinstance(chip_id, str):
            return {
                "success": False,
                "message": "Invalid or missing chipId"
            }
        
        distance = node_data.get('distance')
        battery = node_data.get('battery')
        uptime_ms = node_data.get('uptime_ms', 0)
        node_mac = node_data.get('node_mac')
        role = node_data.get('role')
        
        storage.update_sensor_data(
            chip_id=chip_id,
            distance=distance,
            battery=battery,
            uptime_ms=uptime_ms,
            node_mac=node_mac,
            role=role
        )
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        display_name = storage.get_display_name(chip_id)
        print(f"[{timestamp}] Data from '{display_name}': distance={distance}, battery={battery}%")
        
        return {
            "success": True,
            "chip_id": chip_id.upper()
        }
    
    
    def receive_single_data(self, chip_id, distance, battery, uptime_ms=0, node_mac=None, role=None):
       
        node_data = {
            "chipId": chip_id,
            "distance": distance,
            "battery": battery,
            "uptime_ms": uptime_ms,
            "node_mac": node_mac,
            "role": role
        }
        
        return self._process_single_node(node_data)


esp_receiver = ESPDataReceiver()


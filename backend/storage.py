

from datetime import datetime
from collections import deque

from battery_logger import log_battery_data
BIN_BASELINES = {
    "823C": 30.8,   
    "8AB8": 38.3,   
    "9D58": 37.9   
}


def calculate_fill_percentage(chip_id, distance):
  
    chip_id = chip_id.upper()
    
    if chip_id not in BIN_BASELINES or distance is None:
        return None
    
    baseline = BIN_BASELINES[chip_id]
    fill_percentage = max(0, min(100, ((baseline - distance) / baseline) * 100))
    
    return fill_percentage


class NodeStorage:
    
    def __init__(self, max_history_per_node=100):
     
        self._nodes = {}  # Main storage: {chip_id: node_data}
        self.max_history = max_history_per_node
    
    
    # ==================== NODE MANAGEMENT ====================
    
    def get_or_create_node(self, chip_id, node_mac=None, role=None):
      
        chip_id = chip_id.upper()
        
        if chip_id not in self._nodes:
            # Auto-register new node
            now = datetime.now()
            self._nodes[chip_id] = {
                "chip_id": chip_id,
                "name": None,  # None means use chip_id as display name
                "node_mac": node_mac,
                "role": role,
                "distance": None,
                "battery": None,
                # Continuous uptime tracked by backend (ms)
                "uptime_ms": None,
                # Last uptime value reported by device for a cycle (ms)
                "last_cycle_uptime_ms": None,
                "last_update": None,
                "first_seen": now,  # Track when node first came online
                "last_online_period_start": now,  # Track current online session start
                "status": "waiting",
                "created_at": now.strftime('%Y-%m-%d %H:%M:%S'),
                "history": deque(maxlen=self.max_history)
            }
            print(f"[Auto-registered] New node: {chip_id}")
        
        return self._nodes[chip_id]
    
    
    def delete_node(self, chip_id):
       
        chip_id = chip_id.upper()
        if chip_id in self._nodes:
            del self._nodes[chip_id]
            return True
        return False
    
    
    def node_exists(self, chip_id):
        return chip_id.upper() in self._nodes
    
    
    def get_node_count(self):
        return len(self._nodes)
    
    
    
    def update_sensor_data(self, chip_id, distance, battery, uptime_ms, node_mac=None, role=None):
        chip_id = chip_id.upper()

        node = self.get_or_create_node(chip_id, node_mac, role)

        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

        was_offline = node["status"] != "active"
        if was_offline:
            node["last_online_period_start"] = now

        uptime_duration = now - node["last_online_period_start"]
        calculated_uptime_ms = int(uptime_duration.total_seconds() * 1000)

        node["distance"] = distance
        node["battery"] = battery
        node["uptime_ms"] = calculated_uptime_ms
        node["last_cycle_uptime_ms"] = uptime_ms
        node["last_update"] = timestamp
        node["status"] = "active"

        log_battery_data(
            chip_id=chip_id,
            node_mac=node_mac or node.get("node_mac"),
            role=role or node.get("role"),
            battery=battery,
            distance=distance,
            uptime_ms=uptime_ms,
            timestamp=timestamp,
        )

        if node_mac:
            node["node_mac"] = node_mac
        if role:
            node["role"] = role

        fill_percentage = calculate_fill_percentage(chip_id, distance)
        history_entry = {
            "timestamp": timestamp,
            "distance": distance,
            "fill_percentage": fill_percentage,
            "battery": battery,
            "uptime_ms": uptime_ms
        }
        node["history"].append(history_entry)

        return True
    
    
    def update_node_name(self, chip_id, name):
        chip_id = chip_id.upper()
        if chip_id not in self._nodes:
            return False
        
        self._nodes[chip_id]["name"] = name if name and name.strip() else None
        return True
    
    

    def _calculate_uptime_status(self, node):
        if not node["last_update"]:
            node["status"] = "offline"
            return {
                "state": "offline",
                "seconds_since_update": None
            }

        last_update_time = datetime.strptime(node["last_update"], '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        time_diff = (now - last_update_time).total_seconds()

        if time_diff > 30:
            if node["status"] == "active":
                node["status"] = "offline"
            return {
                "state": "offline",
                "seconds_since_update": int(time_diff)
            }
        else:
            return {
                "state": "online",
                "seconds_since_update": int(time_diff)
            }

    def get_display_name(self, chip_id):
        chip_id = chip_id.upper()
        if chip_id not in self._nodes:
            return chip_id
        
        name = self._nodes[chip_id].get("name")
        return name if name else chip_id
    
    
    def get_dashboard_summary(self, chip_id):
        chip_id = chip_id.upper()
        if chip_id not in self._nodes:
            return None

        node = self._nodes[chip_id]

        uptime_status = self._calculate_uptime_status(node)

        return {
            "name": self.get_display_name(chip_id),
            "distance": node["distance"],
            "battery": node["battery"],
            "role": node["role"],
            "chip_id": node["chip_id"],
            "last_update": node["last_update"],
            "uptime_ms": node["uptime_ms"],
            "last_cycle_uptime_ms": node["last_cycle_uptime_ms"],
            "uptime_status": uptime_status
        }
    
    
    def get_all_dashboard_summary(self):
        return [self.get_dashboard_summary(chip_id) for chip_id in self._nodes.keys()]
    
    
    def get_node_history(self, chip_id):
        chip_id = chip_id.upper()
        if chip_id not in self._nodes:
            return None
        
        return list(self._nodes[chip_id]["history"])
    
    
    def get_node_full(self, chip_id):
        chip_id = chip_id.upper()
        if chip_id not in self._nodes:
            return None
        
        node = self._nodes[chip_id]
        return {
            "chip_id": node["chip_id"],
            "name": self.get_display_name(chip_id),
            "node_mac": node["node_mac"],
            "role": node["role"],
            "distance": node["distance"],
            "battery": node["battery"],
            "uptime_ms": node["uptime_ms"],
            "last_cycle_uptime_ms": node["last_cycle_uptime_ms"],
            "last_update": node["last_update"],
            "status": node["status"],
            "created_at": node["created_at"],
            "history": list(node["history"])
        }
    
    
    
    def get_active_node_count(self):
        return sum(1 for node in self._nodes.values() if node["status"] == "active")
    
    
    def get_node_statistics(self, chip_id):
        chip_id = chip_id.upper()
        if chip_id not in self._nodes:
            return None
        
        history = list(self._nodes[chip_id]["history"])
        
        if not history:
            return {
                "total_readings": 0,
                "avg_distance": None,
                "min_distance": None,
                "max_distance": None
            }
        
        distances = [entry["distance"] for entry in history if entry["distance"] is not None]
        
        if not distances:
            return {
                "total_readings": len(history),
                "avg_distance": None,
                "min_distance": None,
                "max_distance": None
            }
        
        return {
            "total_readings": len(history),
            "avg_distance": sum(distances) / len(distances),
            "min_distance": min(distances),
            "max_distance": max(distances)
        }

    def get_average_cycle_uptime_ms(self, per_node_limit=20):
        uptimes = []
        for node in self._nodes.values():
            history = list(node["history"])
            if not history:
                continue
            recent = history[-per_node_limit:]
            for entry in recent:
                value = entry.get("uptime_ms")
                if isinstance(value, (int, float)):
                    uptimes.append(value)

        if not uptimes:
            return None

        return sum(uptimes) / len(uptimes)
    
    
    
    def clear_all(self):
        self._nodes = {}


storage = NodeStorage()



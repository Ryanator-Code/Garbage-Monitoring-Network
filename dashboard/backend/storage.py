"""
In-Memory Data Storage for ESP32 Sensor Network

This module handles all data storage and retrieval operations for sensor nodes.
No network/API logic - purely data management.
"""

from datetime import datetime
from collections import deque
import uuid


class NodeStorage:
    """In-memory storage for sensor nodes"""
    
    def __init__(self, max_history_per_node=100):
        """
        Initialize the node storage
        
        Args:
            max_history_per_node (int): Maximum number of historical readings to keep per node
        """
        self._nodes = {}  # Main storage: {node_id: node_data}
        self.max_history = max_history_per_node
    
    
    # ==================== NODE MANAGEMENT ====================
    
    def create_node(self, name, chip_id=None):
        """
        Create a new node
        
        Args:
            name (str): Human-readable name for the node
            chip_id (str): Last 4 digits of ESP32 chip ID (optional)
            
        Returns:
            str: The unique node_id
        """
        node_id = str(uuid.uuid4())[:8]  # Generate short unique ID
        
        # Normalize chip_id to uppercase if provided
        if chip_id:
            chip_id = chip_id.upper()
        
        node = {
            "id": node_id,
            "name": name,
            "chip_id": chip_id,  # Last 4 digits of ESP32 chip ID
            "latest_cm": None,
            "latest_inches": None,
            "last_update": None,
            "boot_count": 0,
            "status": "waiting",  # States: waiting, active, inactive
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "history": deque(maxlen=self.max_history)  # Circular buffer
        }
        
        self._nodes[node_id] = node
        return node_id
    
    
    def delete_node(self, node_id):
        """
        Delete a node
        
        Args:
            node_id (str): The node ID to delete
            
        Returns:
            bool: True if deleted, False if node not found
        """
        if node_id in self._nodes:
            del self._nodes[node_id]
            return True
        return False
    
    
    def node_exists(self, node_id):
        """
        Check if a node exists
        
        Args:
            node_id (str): The node ID to check
            
        Returns:
            bool: True if node exists, False otherwise
        """
        return node_id in self._nodes
    
    
    def get_all_node_ids(self):
        """
        Get list of all node IDs
        
        Returns:
            list: List of all node IDs
        """
        return list(self._nodes.keys())
    
    
    def get_node_count(self):
        """
        Get total number of nodes
        
        Returns:
            int: Number of nodes in storage
        """
        return len(self._nodes)
    
    
    # ==================== DATA UPDATES ====================
    
    def update_sensor_data(self, node_id, cm, inches, boot_count):
        """
        Update a node with new sensor data
        
        Args:
            node_id (str): The node ID to update
            cm (float): Distance in centimeters
            inches (float): Distance in inches
            boot_count (int): Boot/wake cycle count
            
        Returns:
            bool: True if updated successfully, False if node not found
        """
        if node_id not in self._nodes:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update latest values
        self._nodes[node_id]["latest_cm"] = cm
        self._nodes[node_id]["latest_inches"] = inches
        self._nodes[node_id]["last_update"] = timestamp
        self._nodes[node_id]["boot_count"] = boot_count
        self._nodes[node_id]["status"] = "active"
        
        # Add to history (deque automatically removes oldest when full)
        history_entry = {
            "timestamp": timestamp,
            "cm": cm,
            "inches": inches,
            "boot_count": boot_count
        }
        self._nodes[node_id]["history"].append(history_entry)
        
        return True
    
    
    # ==================== DATA RETRIEVAL ====================
    
    def get_node_summary(self, node_id):
        """
        Get node summary data (without history)
        Useful for dashboard lists where you don't need full history
        
        Args:
            node_id (str): The node ID to retrieve
            
        Returns:
            dict or None: Node summary data, or None if not found
        """
        if node_id not in self._nodes:
            return None
        
        node = self._nodes[node_id]
        return {
            "id": node["id"],
            "name": node["name"],
            "chip_id": node["chip_id"],
            "latest_cm": node["latest_cm"],
            "latest_inches": node["latest_inches"],
            "last_update": node["last_update"],
            "boot_count": node["boot_count"],
            "status": node["status"],
            "created_at": node["created_at"]
        }
    
    
    def get_node_full(self, node_id):
        """
        Get complete node data including history
        Useful for detail pages
        
        Args:
            node_id (str): The node ID to retrieve
            
        Returns:
            dict or None: Complete node data, or None if not found
        """
        if node_id not in self._nodes:
            return None
        
        node = self._nodes[node_id]
        return {
            "id": node["id"],
            "name": node["name"],
            "chip_id": node["chip_id"],
            "latest_cm": node["latest_cm"],
            "latest_inches": node["latest_inches"],
            "last_update": node["last_update"],
            "boot_count": node["boot_count"],
            "status": node["status"],
            "created_at": node["created_at"],
            "history": list(node["history"])  # Convert deque to list for JSON
        }
    
    
    def get_all_nodes_summary(self):
        """
        Get summary data for all nodes (without history)
        
        Returns:
            list: List of node summary dictionaries
        """
        return [self.get_node_summary(node_id) for node_id in self._nodes.keys()]
    
    
    def get_node_history(self, node_id):
        """
        Get only the history for a specific node
        
        Args:
            node_id (str): The node ID
            
        Returns:
            list or None: List of history entries, or None if node not found
        """
        if node_id not in self._nodes:
            return None
        
        return list(self._nodes[node_id]["history"])
    
    
    # ==================== STATISTICS ====================
    
    def get_active_node_count(self):
        """
        Get count of active nodes
        
        Returns:
            int: Number of nodes with status 'active'
        """
        return sum(1 for node in self._nodes.values() if node["status"] == "active")
    
    
    def get_node_statistics(self, node_id):
        """
        Calculate statistics for a node's history
        
        Args:
            node_id (str): The node ID
            
        Returns:
            dict or None: Statistics dictionary, or None if node not found
        """
        if node_id not in self._nodes:
            return None
        
        history = list(self._nodes[node_id]["history"])
        
        if not history:
            return {
                "total_readings": 0,
                "avg_cm": None,
                "min_cm": None,
                "max_cm": None
            }
        
        distances = [entry["cm"] for entry in history]
        
        return {
            "total_readings": len(history),
            "avg_cm": sum(distances) / len(distances),
            "min_cm": min(distances),
            "max_cm": max(distances)
        }
    
    
    # ==================== UTILITIES ====================
    
    def clear_all(self):
        """Clear all nodes from storage (useful for testing)"""
        self._nodes = {}
    
    
    def update_node_name(self, node_id, new_name):
        """
        Update a node's name
        
        Args:
            node_id (str): The node ID
            new_name (str): New name for the node
            
        Returns:
            bool: True if updated, False if node not found
        """
        if node_id not in self._nodes:
            return False
        
        self._nodes[node_id]["name"] = new_name
        return True


# ==================== MODULE-LEVEL INSTANCE ====================
# Create a singleton instance for easy import
storage = NodeStorage()


# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    # Example usage demonstration
    
    print("Creating test nodes...")
    node1 = storage.create_node("Living Room Sensor")
    node2 = storage.create_node("Bedroom Sensor")
    
    print(f"\nCreated nodes: {node1}, {node2}")
    print(f"Total nodes: {storage.get_node_count()}")
    
    print("\nAdding sensor data...")
    storage.update_sensor_data(node1, cm=45.5, inches=17.9, boot_count=1)
    storage.update_sensor_data(node1, cm=46.2, inches=18.2, boot_count=2)
    storage.update_sensor_data(node2, cm=30.1, inches=11.8, boot_count=1)
    
    print("\nNode summaries:")
    for node in storage.get_all_nodes_summary():
        print(f"  {node['name']}: {node['latest_cm']} cm - {node['status']}")
    
    print(f"\nNode 1 full data:")
    full_data = storage.get_node_full(node1)
    print(f"  Name: {full_data['name']}")
    print(f"  History entries: {len(full_data['history'])}")
    
    print(f"\nNode 1 statistics:")
    stats = storage.get_node_statistics(node1)
    print(f"  Total readings: {stats['total_readings']}")
    print(f"  Average: {stats['avg_cm']:.2f} cm")
    print(f"  Min: {stats['min_cm']} cm, Max: {stats['max_cm']} cm")
    
    print(f"\nDeleting node 2...")
    storage.delete_node(node2)
    print(f"Total nodes: {storage.get_node_count()}")
"""
ESP32 Data Receiver

Handles incoming sensor data from ESP32 nodes and validates against registered nodes.
ESP32s are identified by the last 4 digits of their chip ID.
"""

from storage import storage
from datetime import datetime


class ESPDataReceiver:
    """Handles data reception from ESP32 devices"""
    
    def __init__(self):
        pass
    
    
    def receive_data(self, chip_id, cm, inches, boot_count):
        """
        Receive and process data from an ESP32
        
        Args:
            chip_id (str): Last 4 digits of ESP32 chip ID (e.g., "A3B7")
            cm (float): Distance measurement in centimeters
            inches (float): Distance measurement in inches
            boot_count (int): Number of times ESP32 has booted/woken
            
        Returns:
            dict: Result with success status and message
                {
                    "success": bool,
                    "message": str,
                    "node_id": str (if successful),
                    "node_name": str (if successful)
                }
        """
        # Validate chip_id format
        if not chip_id or len(chip_id) != 4:
            return {
                "success": False,
                "message": "Invalid chip ID. Must be 4 characters.",
                "error": "INVALID_CHIP_ID"
            }
        
        # Normalize chip_id to uppercase
        chip_id = chip_id.upper()
        
        # Find the node with this chip_id
        node_id = self._find_node_by_chip_id(chip_id)
        
        if not node_id:
            return {
                "success": False,
                "message": f"Node with chip ID '{chip_id}' not registered. Please add it to the dashboard first.",
                "error": "NODE_NOT_REGISTERED",
                "chip_id": chip_id
            }
        
        # Update the node with sensor data
        success = storage.update_sensor_data(node_id, cm, inches, boot_count)
        
        if not success:
            return {
                "success": False,
                "message": "Failed to update node data",
                "error": "UPDATE_FAILED"
            }
        
        # Get node info for response
        node = storage.get_node_summary(node_id)
        
        # Log the data reception
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Data from '{node['name']}' (Chip: {chip_id}): {cm} cm, Boot #{boot_count}")
        
        return {
            "success": True,
            "message": "Data received successfully",
            "node_id": node_id,
            "node_name": node['name']
        }
    
    
    def _find_node_by_chip_id(self, chip_id):
        """
        Find a node by its chip ID
        
        Args:
            chip_id (str): The chip ID to search for
            
        Returns:
            str or None: The node_id if found, None otherwise
        """
        # Get all nodes and check their chip_ids
        all_nodes = storage._nodes  # Direct access for internal use
        
        for node_id, node_data in all_nodes.items():
            if node_data.get("chip_id") == chip_id:
                return node_id
        
        return None
    
    
    def validate_chip_id_available(self, chip_id):
        """
        Check if a chip ID is available (not already registered)
        
        Args:
            chip_id (str): The chip ID to check
            
        Returns:
            dict: Result with availability status
                {
                    "available": bool,
                    "message": str
                }
        """
        if not chip_id or len(chip_id) != 4:
            return {
                "available": False,
                "message": "Invalid chip ID format. Must be 4 characters."
            }
        
        chip_id = chip_id.upper()
        node_id = self._find_node_by_chip_id(chip_id)
        
        if node_id:
            node = storage.get_node_summary(node_id)
            return {
                "available": False,
                "message": f"Chip ID already registered to node '{node['name']}'"
            }
        
        return {
            "available": True,
            "message": "Chip ID is available"
        }
    
    
    def get_chip_id_info(self, chip_id):
        """
        Get information about a chip ID
        
        Args:
            chip_id (str): The chip ID to look up
            
        Returns:
            dict or None: Node information if registered, None otherwise
        """
        chip_id = chip_id.upper()
        node_id = self._find_node_by_chip_id(chip_id)
        
        if not node_id:
            return None
        
        return storage.get_node_summary(node_id)


# Create singleton instance
esp_receiver = ESPDataReceiver()


# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    # Example: Simulating ESP32 data reception
    
    print("Testing ESP32 Data Receiver\n")
    
    # First, we need to add a node with a chip_id
    # (This would normally be done through the API)
    from storage import storage
    
    print("1. Creating a test node with chip ID...")
    node_id = storage.create_node("Living Room Sensor")
    # Manually add chip_id to the node (API will do this)
    storage._nodes[node_id]["chip_id"] = "A3B7"
    print(f"   Created node: {node_id} with chip ID: A3B7\n")
    
    # Test 1: Valid data from registered ESP32
    print("2. Testing valid data from registered ESP32 (A3B7)...")
    result = esp_receiver.receive_data(
        chip_id="a3b7",  # Case insensitive
        cm=45.5,
        inches=17.9,
        boot_count=1
    )
    print(f"   Result: {result}\n")
    
    # Test 2: Data from unregistered ESP32
    print("3. Testing data from unregistered ESP32 (FFFF)...")
    result = esp_receiver.receive_data(
        chip_id="FFFF",
        cm=30.0,
        inches=11.8,
        boot_count=1
    )
    print(f"   Result: {result}\n")
    
    # Test 3: Invalid chip ID format
    print("4. Testing invalid chip ID format...")
    result = esp_receiver.receive_data(
        chip_id="123",  # Too short
        cm=25.0,
        inches=9.8,
        boot_count=1
    )
    print(f"   Result: {result}\n")
    
    # Test 4: Check chip ID availability
    print("5. Checking chip ID availability...")
    result = esp_receiver.validate_chip_id_available("A3B7")
    print(f"   A3B7 available? {result}\n")
    
    result = esp_receiver.validate_chip_id_available("DEAD")
    print(f"   DEAD available? {result}\n")
    
    # Test 5: Get chip ID info
    print("6. Getting chip ID info...")
    info = esp_receiver.get_chip_id_info("A3B7")
    print(f"   Info: {info}")
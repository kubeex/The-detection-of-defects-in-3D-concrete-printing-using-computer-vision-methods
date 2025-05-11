from opcua import Client
from datetime import datetime

class PrinterCommunication:
    def __init__(self, server_url="opc.tcp://192.168.1.100:4840"):
        self.server_url = server_url
        self.client = Client(self.server_url)

        # Tady budou NodeId pro pozici a rychlost (doplň po zjištění)
        self.node_position_x = None
        self.node_position_y = None
        self.node_position_z = None
        self.node_speed = None
        self.connected = False


    def connect(self):
        try:
            self.client.connect()
            self.connected = True
            print("[PrinterComm] Connected to OPC UA server.")

            # TODO: Změnit NodeId podle reálné struktury serveru
            self.node_position_x = self.client.get_node("ns=2;s=Machine.Position.X")
            self.node_position_y = self.client.get_node("ns=2;s=Machine.Position.Y")
            self.node_position_z = self.client.get_node("ns=2;s=Machine.Position.Z")
            self.node_speed = self.client.get_node("ns=2;s=Machine.Speed")

        except Exception as e:
            print(f"[PrinterComm] Connection failed: {e}")
            self.connected = False

    def disconnect(self):
        if self.connected:
            self.client.disconnect()
            print("[PrinterComm] Disconnected.")

    def update_position(self):
        if not self.connected:
            print("[PrinterComm] Not connected.")
            return None

        try:
            pos = {
                "x": self.node_position_x.get_value(),
                "y": self.node_position_y.get_value(),
                "z": self.node_position_z.get_value(),
                "speed": self.node_speed.get_value(),
                "timestamp": datetime.now().isoformat()
            }
            return pos

        except Exception as e:
            print(f"[PrinterComm] Error reading data: {e}")
            return None
    
    def get_current_coords(self):
        """
        Get the current coordinates from the printer.
        :return: A tuple of (x, y, z) coordinates.
        """
        # x = self.node_position_x.get_value(),
        # y = self.node_position_y.get_value(),
        # z = self.node_position_z.get_value(),
        # Simulate getting coordinates from the printer
        x = 100.0
        y = 200.0
        z = 300.0
        return x, y, z
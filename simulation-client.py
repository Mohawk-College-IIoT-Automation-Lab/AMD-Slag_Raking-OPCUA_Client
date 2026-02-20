#!/home/daniil/miniconda3/envs/opcua/bin/python
from asyncua import Client
import asyncio
from enum import StrEnum

# Only needed for access to command line arguments
import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
        QApplication, 
        QWidget,
        QPushButton,
        QPushButton,
        QMainWindow,
        QLabel,
        QVBoxLayout,
        QHBoxLayout,
        QButtonGroup,
        QSizePolicy,
        )

# 1. The Callback Class
class SubscriptionHandler:
    """This class is called by the OPC UA client when data changes."""
    def __init__(self, signal):
        self.signal = signal

    def datachange_notification(self, node, val, data):
        # We emit the Qt Signal to update the UI safely from the background
        self.signal.emit(str(val))

# 2. The Worker Thread
class OPCWorker(QThread):
    value_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, url, node_id, lookup):
        super().__init__()
        self.url = url
        self.node_id = node_id
        self.lookup = lookup
        self.loop = None
        self._client = None

    def run(self):
        """Main entry point for the thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.monitor_opc())

    async def monitor_opc(self):
        try:
            async with Client(url=self.url) as client:
                self._client = client
                node =  client.get_node(self.node_id)
                
                # Setup Subscription
                handler = SubscriptionHandler(self.value_changed)
                subscription = await client.create_subscription(500, handler)
                await subscription.subscribe_data_change(node)

                # Keep the thread alive while the connection is open
                while True:
                    await asyncio.sleep(1)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def write_value(self, index):
        """Thread-safe way to write from the UI"""
        if self._client and self.loop:
            value_to_write = self.lookup[index]
            # Schedules the coroutine to run on the worker's event loop
            asyncio.run_coroutine_threadsafe(
                self._set_node_value(value_to_write), 
                self.loop
            )

    async def _set_node_value(self, val):
        # 1. Guard against 'None' if connection isn't ready yet
        if self._client is None:
            print("Error: Client not connected yet.")
            return

        try:
            # 2. Get the node object (synchronous in asyncua)
            node = self._client.get_node(self.node_id)
            
            # 3. Write the value (asynchronous)
            await node.set_value(val)
            print(f"Successfully wrote {val} to server.")
        except Exception as e:
            self.error_occurred.emit(f"Write failed: {e}")



class State(StrEnum):
    IDLE = "IDLE"
    LADLE_ARRIVED = "LADEL_ARRIVED"
    TILITING = "TILTING"
    RAKING = "RAKING"
    COMPLETE = "COMPLETE"


class MainWindow(QMainWindow):
    def __init__(self, opc_url):
        super().__init__()
        
        self.lookup = {i: state.value for i, state in enumerate(State)}

        self.opc_url = opc_url
        self.node_id = "ns=2;i=10"


        self.setWindowTitle("Slag Raking State Control")
        
        # Layouts
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)

        # Create a Button Group
        self.state_group = QButtonGroup(self)
        self.state_group.setExclusive(True) # Ensure only one button i s"down"

        # Push Buttons for State Control
        self.button_idle = QPushButton("IDLE")
        self.button_ladle = QPushButton("LADLE_ARRIVED")
        self.button_tilting = QPushButton("TILTING")
        self.button_raking = QPushButton("RAKING")
        self.button_complete = QPushButton("COMPLETE")
        self.button_exit = QPushButton("Exit Simulation") # Button to stop simulation and exit
        
        self.state_buttons = [
                self.button_idle,
                self.button_ladle,
                self.button_tilting,
                self.button_raking,
                self.button_complete,
                ]


        # Make latching
        for button in self.state_buttons:
            button.setCheckable(True)


        # Add buttons to the Group
        for i, button in enumerate(self.state_buttons):
            self.state_group.addButton(button, i)


        # Set Initial State for the system
        self.button_idle.setChecked(True)
        
        # Connect id Click signal of the button group to the self.update_state setLayout
        self.state_group.idClicked.connect(self.update_state)
        # Label to display current state as read from the OPC UA server
        self.process_state = QLabel("click here")
        self.process_state.setAlignment(Qt.AlignmentFlag.AlignCenter)


        for button in self.state_buttons:
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            font = button.font()
            font.setPointSize(12)
            font.setBold(True)
            button.setFont(font)


            left_layout.addWidget(button)

        right_layout.addWidget(self.process_state)
        right_layout.addWidget(self.button_exit)


        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # 5. Visual Styling (Optional but helpful)
        self.setStyleSheet("""
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
        """)

        self.worker = OPCWorker(self.opc_url, self.node_id, self.lookup)
        # Connect the subscription signal directly to your label
        self.worker.value_changed.connect(self.process_state.setText)
        self.worker.start()
        
    # Updated update_state
    def update_state(self, val_id):
        """Clean and fast: just sends the command to the background"""
        print(f"UI requesting change to: {val_id}")
        self.worker.write_value(val_id)


    async def write_opc_value(self, value):
        """The actual OPC UA async communication"""
        try:
            async with Client(url=self.opc_url) as client:
                node = client.get_node(self.node_id)
                # Setting the value (assumes the node is an Integer type)
                await node.set_value(self.lookup[value])
        except Exception as e:
            print(f"OPC UA Error: {e}")

    async def read_opc_value(self):
        try:
            async with Client(url=self.opc_url) as client:
                node = client.get_node(self.node_id)
                return await node.read_value()
        except Exception as e:
            print(f"OPC UA Error: {e}")
            return None
                


app = QApplication(sys.argv)

url = "opc.tcp://127.0.0.1:49320/FTLinxGateway"

# Create a Qt widget, which will be our window.
window = MainWindow(url)
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()


# Your application won't reach here until you exit and the event
# loop has stopped.

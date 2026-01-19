#!/home/daniil/miniconda3/envs/opcua/bin/python
from PyQt6.QtCore import QSize, Qt
import asyncio
from asyncua import Client
from PyQt6.QtWidgets import (
        QApplication, 
        QWidget,
        QPushButton,
        QPushButton,
        QMainWindow,
        QLabel,
        QComboBox,
        QListWidget,
        QVBoxLayout,
        QHBoxLayout,
        QButtonGroup,
        QSizePolicy,
        )
# Only needed for access to command line arguments
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # self.opc_url = opc_url
        self.node_id = "ns=2;i=2"


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
        self.button_idle = QPushButton("No Laddle")
        self.button_laddle = QPushButton("Laddle Arrived")
        self.button_tilting = QPushButton("Laddle Tilting")
        self.button_raking = QPushButton("Raking in progress")
        self.button_finish = QPushButton("Raking finished")
        self.button_exit = QPushButton("Exit Simulation") # Button to stop simulation and exit
        
        self.state_buttons = [
                self.button_idle,
                self.button_laddle,
                self.button_tilting,
                self.button_raking,
                self.button_finish,
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

        # Signal for the Buttons
        self.button_idle.clicked.connect(lambda: self.update_state(0))

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
        
    def update_state(self, val):
            """Wrapper to run the async write task"""
            print(f"Switching state to: {val}")
            # asyncio.run(self.write_opc_value(val))
            self.process_state.setText(f"Last Command: {val}")

    async def write_opc_value(self, value):
        """The actual OPC UA async communication"""
        try:
            async with Client(url=self.opc_url) as client:
                node = client.get_node(self.node_id)
                # Setting the value (assumes the node is an Integer type)
                await node.set_value(value)
        except Exception as e:
            print(f"OPC UA Error: {e}")


app = QApplication(sys.argv)

url = "opc.tcp://127.0.0.1:4840"

# Create a Qt widget, which will be our window.
window = MainWindow()
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()


# Your application won't reach here until you exit and the event
# loop has stopped.

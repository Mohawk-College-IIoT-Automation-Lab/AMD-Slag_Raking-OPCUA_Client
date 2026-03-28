#!/home/daniil/miniconda3/envs/opcua/bin/python
import sys
import asyncio
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QTextEdit)
from PyQt6.QtCore import Qt
from qasync import QEventLoop, asyncSlot
from asyncua import Client, ua, Node
import consts 

class SimulationGUI(QWidget):
    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint
        self.client = Client(self.endpoint)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Ladle Simulation Control")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout()

        # Heat ID Input
        self.id_label = QLabel("Heat ID (Positive Integer):")
        self.heat_id_input = QLineEdit()
        self.heat_id_input.setPlaceholderText("Enter Heat ID...")
        layout.addWidget(self.id_label)
        layout.addWidget(self.heat_id_input)

        # Toggle Button
        self.tilt_btn = QPushButton("Ladle Idle")
        self.tilt_btn.setCheckable(True)
        self.tilt_btn.setFixedHeight(60)
        self.tilt_btn.setStyleSheet("background-color: #f0f0f0;")
        self.tilt_btn.clicked.connect(self.handle_toggle)
        layout.addWidget(self.tilt_btn)

        # Logger/Status Box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(QLabel("System Logs:"))
        layout.addWidget(self.log_box)

        self.setLayout(layout)

    def log(self, message):
        self.log_box.append(f">> {message}")

    def validate_input(self):
        val = self.heat_id_input.text()
        if val.isdigit() and int(val) > 0:
            return int(val)
        return None

    @asyncSlot()
    async def handle_toggle(self):
        heat_id = self.validate_input()
        
        # If trying to start (press button)
        if self.tilt_btn.isChecked():
            if heat_id is None:
                self.log("Error: Please enter a valid Heat ID (>0) before starting.")
                self.tilt_btn.setChecked(False) # Reset button
                return
            
            # Lock input and change UI
            self.heat_id_input.setEnabled(False)
            self.tilt_btn.setText("Raking in progress")
            self.tilt_btn.setStyleSheet("background-color: green; color: white;")
            await self.write_to_opc(True, heat_id)
        
        # If trying to stop (release button)
        else:
            self.heat_id_input.setEnabled(True)
            self.tilt_btn.setText("Ladle Idle")
            self.tilt_btn.setStyleSheet("background-color: #f0f0f0; color: black;")
            await self.write_to_opc(False, heat_id)

    async def write_to_opc(self, state, heat_id):
        try:
            async with Client(self.endpoint) as client:
                # Get Node References
                rake_state_node : Node = client.get_node(consts.RAKE_HOME_STATE_NODEID)
                heat_id_node : Node = client.get_node(consts.HEAT_ID_NODEID)

                # Write back
                await rake_state_node.set_value(not bool(state), ua.VariantType.Boolean)
                await heat_id_node.set_value(float(heat_id), ua.VariantType.Double)
                
                self.log(f"Success: State={state}, HeatID={heat_id} written to server.")
        
        except Exception as e:
            self.log(f"OPC UA Error: {str(e)}")

async def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    gui = SimulationGUI(consts.ENDPOINT)
    gui.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    asyncio.run(main())

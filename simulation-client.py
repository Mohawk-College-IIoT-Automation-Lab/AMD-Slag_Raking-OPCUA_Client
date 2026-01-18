#!/home/daniil/miniconda3/envs/opcua/bin/python
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
        QApplication, 
        QWidget,
        QPushButton,
        QMainWindow,
        QLabel,
        QComboBox,
        QListWidget,
        QVBoxLayout,
        QHBoxLayout,
        )
# Only needed for access to command line arguments
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Slag Raking State Control")
        
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        # Add push button for states
        self.button_idle = QPushButton("No Laddle")
        self.button_laddle = QPushButton("Laddle Arrived")
        self.button_tilting = QPushButton("Laddle Tilting")
        self.button_raking = QPushButton("Raking in progress")
        self.button_finish = QPushButton("Raking finished")
        self.button_exit = QPushButton("Exit Simulation") # Button to stop simulation and exit

        # Label to display current state as read from the OPC UA server
        self.process_state = QLabel("click here")
        self.process_state.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(self.button_idle)
        left_layout.addWidget(self.button_laddle)
        left_layout.addWidget(self.button_tilting)
        left_layout.addWidget(self.button_raking)
        left_layout.addWidget(self.button_finish)
        

        right_layout.addWidget(self.process_state)
        right_layout.addWidget(self.button_exit)


        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        

# from PyQt6.QtWidgets import QPushButton
#
# def on_toggle(is_checked):
#     if is_checked:
#         button.setText("ON")
#         button.setStyleSheet("background-color: green;")
#     else:
#         button.setText("OFF")
#         button.setStyleSheet("background-color: red;")
#
# button = QPushButton("OFF")
# button.setCheckable(True)
# button.toggled.connect(on_toggle)
    #     self.button_is_checked = True
    #
    #     self.button = QPushButton("Idle")
    #
    #     self.button.setCheckable(True)
    #     self.button.clicked.connect(self.the_button_was_clicked)
    #     self.button.setChecked(self.button_is_checked)
    #
    #     # Set the central widget of the window
    #     self.setCentralWidget(self.button)
    #
    # def the_button_was_clicked(self, checked):
    #     self.button_is_checked = checked
    #     print(self.button_is_checked)
    #
    #     # to make button unclickable
    #     self.button.setEnabled(False)


# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

# Create a Qt widget, which will be our window.
window = MainWindow()
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()


# Your application won't reach here until you exit and the event
# loop has stopped.

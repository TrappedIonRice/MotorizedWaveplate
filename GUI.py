import sys
import os
import serial
import time
import datetime
import matplotlib
import json

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


# Attempt to initialize serial connection
def initialize_serial():
    try:
        arduinoData = serial.Serial('COM6', 9600)
        time.sleep(2)
        print("Arduino connected")
        return arduinoData
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None


arduinoData = initialize_serial()

# Update parameters function
def update_parameters(command, value):
    if arduinoData and arduinoData.is_open:
        try:
            if command in ['S', 'P', 'I', 'D', 'E', 'T']:
                arduinoData.write(f"{command}{value}\n".encode())
                time.sleep(0.1)  # Allow some time for the Arduino to process the command
        except serial.SerialException as e:
            print(f"Error writing to serial port: {e}")


Voltage = []
Setpoint = []
TimeStamps = []
ElapsedTime = []
Error = []

first_update = True
def ensure_data_folder_exists():
    folder_name = "Time & Voltage Data"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

class PIDControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.Kp = 0.8
        self.Ki = 0.5
        self.Kd = 0
        self.setpoint_value = 2.5
        self.sample_time_value = 2000
        self.num_points = 200
        self.PIDenabled = False  # PID is initially enabled
        self.load_settings()

        self.data_folder = ensure_data_folder_exists()
        self.data_file = None
        self.data_file_count = 0  # Counter for data points
        self.initDataFile()

        self.start_time = time.time()
        self.initUI()
        self.initPlot()

    def initUI(self):
        self.setWindowTitle('PID Control')
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QVBoxLayout()

        # Horizontal layout for toolbar and controls
        toolbar_and_controls_layout = QHBoxLayout()

        # Error Display
        self.error_label = QLabel('Error: 0.00')
        self.error_label.setStyleSheet("font-size: 16px; margin-right: 10px;")
        toolbar_and_controls_layout.addWidget(self.error_label)

        # Enable/Disable PID
        self.enable_button = QPushButton('PID Disabled')
        self.enable_button.setStyleSheet("font-size: 16px;")
        self.enable_button.clicked.connect(self.toggle_pid)
        toolbar_and_controls_layout.addWidget(self.enable_button)

        # Setpoint Input
        setpoint_label = QLabel('Set Point:')
        setpoint_label.setStyleSheet("font-size: 16px;")
        self.setpoint_input = QLineEdit()
        self.setpoint_input.setStyleSheet("font-size: 16px; width: 60px;")
        self.setpoint_input.returnPressed.connect(lambda: self.update_pid_param('S', self.setpoint_input.text()))

        toolbar_and_controls_layout.addWidget(setpoint_label)
        toolbar_and_controls_layout.addWidget(self.setpoint_input)

        # PID Inputs: Kp, Ki, Kd
        p_label = QLabel('Kp:')
        p_label.setStyleSheet("font-size: 16px;")
        self.p_input = QLineEdit()
        self.p_input.setStyleSheet("font-size: 16px; width: 60px;")
        self.p_input.returnPressed.connect(lambda: self.update_pid_param('P', self.p_input.text()))

        i_label = QLabel('Ki:')
        i_label.setStyleSheet("font-size: 16px;")
        self.i_input = QLineEdit()
        self.i_input.setStyleSheet("font-size: 16px; width: 60px;")
        self.i_input.returnPressed.connect(lambda: self.update_pid_param('I', self.i_input.text()))

        d_label = QLabel('Kd:')
        d_label.setStyleSheet("font-size: 16px;")
        self.d_input = QLineEdit()
        self.d_input.setStyleSheet("font-size: 16px; width: 60px;")
        self.d_input.returnPressed.connect(lambda: self.update_pid_param('D', self.d_input.text()))

        # Sample Time
        sample_time_label = QLabel('Sample Time (ms):')
        sample_time_label.setStyleSheet("font-size: 16px;")
        self.sample_time_input = QLineEdit()
        self.sample_time_input.setStyleSheet("font-size: 16px; width: 60px;")
        self.sample_time_input.returnPressed.connect(lambda: self.update_pid_param('T', self.sample_time_input.text()))

        # Number of Points to Plot
        points_label = QLabel('Number of Data Points:')
        points_label.setStyleSheet(f"font-size: 16px;")
        self.points_input = QLineEdit()
        self.points_input.setStyleSheet(f"font-size: 16px;")
        self.points_input.returnPressed.connect(self.update_num_points)

        toolbar_and_controls_layout.addWidget(p_label)
        toolbar_and_controls_layout.addWidget(self.p_input)
        toolbar_and_controls_layout.addWidget(i_label)
        toolbar_and_controls_layout.addWidget(self.i_input)
        toolbar_and_controls_layout.addWidget(d_label)
        toolbar_and_controls_layout.addWidget(self.d_input)
        toolbar_and_controls_layout.addWidget(sample_time_label)
        toolbar_and_controls_layout.addWidget(self.sample_time_input)
        toolbar_and_controls_layout.addWidget(points_label)
        toolbar_and_controls_layout.addWidget(self.points_input)

        # Clear Graph Button
        clear_graph_button = QPushButton('Clear Graph')
        clear_graph_button.setStyleSheet("font-size: 16px;")
        clear_graph_button.clicked.connect(self.clear_graph)
        toolbar_and_controls_layout.addWidget(clear_graph_button)

        self.setpoint_input.setText(str(self.setpoint_value))
        self.p_input.setText(str(self.Kp))
        self.i_input.setText(str(self.Ki))
        self.d_input.setText(str(self.Kd))
        self.sample_time_input.setText(str(self.sample_time_value))
        self.points_input.setText(str(self.num_points))

        self.setpoint_input.setValidator(QDoubleValidator(0.5, 3.5, 3))  # Float: 0.5 to 3.5
        self.p_input.setValidator(QDoubleValidator(0.0, 1000.0, 3))  # Allow any reasonable float
        self.i_input.setValidator(QDoubleValidator(0, 1000.0, 3))
        self.d_input.setValidator(QDoubleValidator(0, 1000.0, 3))
        self.sample_time_input.setValidator(QIntValidator(1500, 10000))  # Integer: 1500 to 10000
        self.points_input.setValidator(QIntValidator(10, 1000))  # Integer: 10 to 1000

        # Add toolbar_and_controls_layout to main_layout
        main_layout.addLayout(toolbar_and_controls_layout)

        # Set the main layout
        self.setLayout(main_layout)

    def initPlot(self):
        global fig, ax, line1, line2
        fig, ax = plt.subplots()
        line1, = ax.plot([], [], 'ro-', label='Actual Voltage', markersize=2, linewidth=1)
        line2, = ax.plot([], [], 'bo-', label='Setpoint', markersize=2, linewidth=1)
        ax.set_xlim(0, self.sample_time_value*self.num_points/1000)
        ax.set_title('Real-time Arduino Data', fontsize=8)
        ax.set_ylabel('Voltage (V)', fontsize=8)
        ax.set_xlabel('Time (s)', fontsize=8)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.legend(fontsize=6)
        ax.grid(True)

        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Add the toolbar and canvas to the main layout
        layout = self.layout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def initDataFile(self):
        if self.data_file:
            self.data_file.close()
        # Create a new data file with a timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_filename = os.path.join(self.data_folder, f"data_log_{timestamp}.txt")
        self.data_file = open(self.data_filename, "w")
        self.data_file.write("Time(s)\tVoltage(V)\tSet Point(V)\t Error\n")  # Write headers

    def save_settings(self):
        settings = {
            "Setpoint": self.setpoint_value,
            "Kp": self.Kp,
            "Ki": self.Ki,
            "Kd": self.Kd,
            "Sample_time": self.sample_time_value,
            "Num_points": self.num_points
        }
        with open("settings.json", "w") as file:
            json.dump(settings, file)

    def load_settings(self):
        try:
            with open("settings.json", "r") as file:
                settings = json.load(file)
                self.setpoint_value = float(settings.get("Setpoint", 2.5))
                self.Kp = float(settings.get("Kp", 0.8))
                self.Ki = float(settings.get("Ki", 0.5))
                self.Kd = float(settings.get("Kd", 0.0))
                self.sample_time_value = int(settings.get("Sample_time", 2000))
                self.num_points = int(settings.get("Num_points", 200))
        except FileNotFoundError:
            pass

    def closeEvent(self, event):
        self.save_settings()  # Save current settings
        super().closeEvent(event)  # Call the parent class's closeEvent

    def toggle_pid(self):
        self.PIDenabled = not self.PIDenabled  # Toggle PID state
        update_parameters('E', int(self.PIDenabled))  # Send enable/disable command to Arduino
        self.enable_button.setText('PID Enabled' if self.PIDenabled else 'PID Disabled')  # Update button text

        # Log the manual toggle event
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.PIDenabled:
            self.data_file.write(f"Event: PID Enabled manually at {current_time}\n")
        else:
            self.data_file.write(f"Event: PID Disabled manually at {current_time}\n")
        self.data_file.flush()

    def update_num_points(self):
        self.num_points = int(self.points_input.text())

    def update_pid_param(self, param, value):
        update_parameters(param, value)
        if param == 'P':
            self.Kp = value
            self.p_input.setText(str(self.Kp))  # Update display
        elif param == 'I':
            self.Ki = value
            self.i_input.setText(str(self.Ki))  # Update display
        elif param == 'D':
            self.Kd = value
            self.d_input.setText(str(self.Kd))  # Update display
        elif param == 'S':
            self.setpoint_value = value
            self.setpoint_input.setText(str(self.setpoint_value))  # Update display
        elif param == 'T':
            self.sample_time_value = value
            self.sample_time_input.setText(str(self.sample_time_value))  # Update display

    def clear_graph(self):
        global Voltage, Setpoint, TimeStamps, Error
        Voltage.clear()
        Setpoint.clear()
        TimeStamps.clear()
        Error.clear()
        line1.set_data([], [])
        line2.set_data([], [])
        self.canvas.draw()

    def __del__(self):
        self.data_file.close()

def init():
    line1.set_data([], [])
    line2.set_data([], [])
    return line1, line2


def update(frame):
    global arduinoData, first_update
    if arduinoData and arduinoData.is_open:
        try:
            if arduinoData.in_waiting > 0:  # Check if there is data available to read
                arduinoString = arduinoData.readline().decode('utf-8').rstrip()  # Read and decode the line of text from the serial port
                try:
                    values = arduinoString.split()
                    if len(values) != 2:
                        raise ValueError(f"Expected 2 values, got {len(values)}: {values}")
                    actualVoltage, setpoint = map(float, values)  # Parse the string to get both values

                    # Append data and time
                    Voltage.append(actualVoltage)
                    Setpoint.append(setpoint)
                    elapsed_time = time.time() - pid_app.start_time
                    TimeStamps.append(elapsed_time)

                    # Calculate error
                    error = actualVoltage - setpoint
                    Error.append(error)
                    pid_app.error_label.setText(f'Error: {error:.2f}')

                    # Log warning if error exceeds 5V
                    if abs(actualVoltage) > 4 and pid_app.PIDenabled:  # Check if PID is currently enabled
                        pid_app.PIDenabled = False  # Disable PID
                        update_parameters('E', 0)  # Send command to disable PID
                        pid_app.enable_button.setText('PID Disabled')  # Update button text
                        pid_app.setStyleSheet('background-color: red;')  # Change GUI background

                        # Log the event in the data file
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        pid_app.data_file.write(f"Event: PID Disabled due to Voltage Limit at {current_time}\n")
                        pid_app.data_file.flush()  # Ensure the event is written immediately

                        print(f"Warning: PID Disabled due to Voltage Limit at {current_time}\n")

                    else:
                        pid_app.setStyleSheet('')

                    # Save data to file
                    pid_app.data_file.write(f"{elapsed_time:.2f}\t{actualVoltage:.4f}\t{setpoint:.4f}\t{error:.2f}\n")
                    pid_app.data_file.flush()  # Ensure data is written to file immediately

                    pid_app.data_file_count += 1

                    # Check if the file has reached 50,000 points / create a new file
                    if pid_app.data_file_count >= 50000:
                        pid_app.initDataFile()

                    # Trim data lists to the specified number of points
                    while len(Voltage) > pid_app.num_points:
                        Voltage.pop(0)
                        Setpoint.pop(0)
                        TimeStamps.pop(0)
                        Error.pop(0)

                    line1.set_data(TimeStamps, Voltage)
                    line2.set_data(TimeStamps, Setpoint)

                    # Adjust x,y-axis limits dynamically
                    if Voltage and Setpoint:  # Ensure lists are not empty
                        min_voltage = min(min(Voltage), min(Setpoint)) - 0.1
                        max_voltage = max(max(Voltage), max(Setpoint)) + 0.1
                        ax.set_ylim(min_voltage, max_voltage)
                        ax.set_xlim(min(TimeStamps), max(TimeStamps))

                    if first_update:
                        pid_app.clear_graph()  # Ensures line1, line2, Voltage, and Setpoint are the same length for plotting
                        first_update = False
                    else:
                        pid_app.canvas.draw()
                except ValueError as e:
                    print(f"Error parsing data: {e}")  # Debug: print non-numeric data or parsing issues
        except serial.SerialException as e:
            print(f"Error reading from serial port: {e}")
            arduinoData.close()
            arduinoData = initialize_serial()  # Attempt to reconnect if the COM port is disconnected
    return line1, line2

# Initialize the plot
fig, ax = plt.subplots()

# Start the GUI application
app = QApplication(sys.argv)
pid_app = PIDControlApp()
pid_app.show()

# Start animation
ani = animation.FuncAnimation(fig, update, init_func=init, blit=False, interval=1000, cache_frame_data=False)

# Run the Qt application event loop
sys.exit(app.exec_())

# Close the serial connection when done
if arduinoData and arduinoData.is_open:
    arduinoData.close()

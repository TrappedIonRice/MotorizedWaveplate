import sys
import numpy as np
import serial
import time
import datetime
import matplotlib

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpacerItem, QSizePolicy, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# Constants for the percentage error calculation
VOLTAGE_MIN = 0.560
VOLTAGE_MAX = 4.680

# Initial PID parameters
Kp = 3
Ki = 0.3
Kd = 0.0
pidSampleTime = 2000  # Initial PID sample time in milliseconds

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
Error = []
cnt = 0
PIDenabled = True  # Variable to control the PID
num_points = 200  # Default number of data points to plot

class PIDControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initPlot()
        self.initDataFile()

    def initUI(self):
        self.setWindowTitle('PID Control')
        self.setGeometry(100, 100, 1200, 800)

        layout = QHBoxLayout()

        font_size = 16  # Base font size for GUI elements

        # Control area
        control_layout = QVBoxLayout()

        # Current Settings Display
        current_settings_label = QLabel('Current Settings:')
        current_settings_label.setStyleSheet(f"font-size: {font_size}px;")
        control_layout.addWidget(current_settings_label)

        self.current_setpoint_label = QLabel(f'Set Point: 0')
        self.current_setpoint_label.setStyleSheet(f"font-size: {font_size}px;")
        control_layout.addWidget(self.current_setpoint_label)

        self.current_kp_label = QLabel(f'Kp: {Kp}')
        self.current_kp_label.setStyleSheet(f"font-size: {font_size}px;")
        control_layout.addWidget(self.current_kp_label)

        self.current_ki_label = QLabel(f'Ki: {Ki}')
        self.current_ki_label.setStyleSheet(f"font-size: {font_size}px;")
        control_layout.addWidget(self.current_ki_label)

        self.current_kd_label = QLabel(f'Kd: {Kd}')
        self.current_kd_label.setStyleSheet(f"font-size: {font_size}px;")
        control_layout.addWidget(self.current_kd_label)

        self.current_sample_time_label = QLabel(f'Sample Time: {pidSampleTime} ms')
        self.current_sample_time_label.setStyleSheet(f"font-size: {font_size}px;")
        control_layout.addWidget(self.current_sample_time_label)

        self.error_label = QLabel('Error: 0.00%')
        self.error_label.setStyleSheet(f"font-size: {font_size}px;")
        control_layout.addWidget(self.error_label)

        # Add spacer
        control_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Setpoint
        setpoint_label = QLabel('Set Point:')
        setpoint_label.setStyleSheet(f"font-size: {font_size}px;")
        self.setpoint_input = QLineEdit()
        self.setpoint_input.setStyleSheet(f"font-size: {font_size}px;")
        self.setpoint_input.setText("0")
        setpoint_button = QPushButton('Update')
        setpoint_button.setStyleSheet(f"font-size: {font_size}px;")
        setpoint_button.clicked.connect(lambda: self.update_setpoint())

        setpoint_layout = QHBoxLayout()
        setpoint_layout.addWidget(setpoint_label)
        setpoint_layout.addWidget(self.setpoint_input)
        setpoint_layout.addWidget(setpoint_button)
        control_layout.addLayout(setpoint_layout)

        # Proportional
        p_label = QLabel('Kp:')
        p_label.setStyleSheet(f"font-size: {font_size}px;")
        self.p_input = QLineEdit()
        self.p_input.setStyleSheet(f"font-size: {font_size}px;")
        p_button = QPushButton('Update')
        p_button.setStyleSheet(f"font-size: {font_size}px;")
        p_button.clicked.connect(lambda: self.update_pid('P', self.p_input.text()))

        p_layout = QHBoxLayout()
        p_layout.addWidget(p_label)
        p_layout.addWidget(self.p_input)
        p_layout.addWidget(p_button)
        control_layout.addLayout(p_layout)

        # Integral
        i_label = QLabel('Ki:')
        i_label.setStyleSheet(f"font-size: {font_size}px;")
        self.i_input = QLineEdit()
        self.i_input.setStyleSheet(f"font-size: {font_size}px;")
        i_button = QPushButton('Update')
        i_button.setStyleSheet(f"font-size: {font_size}px;")
        i_button.clicked.connect(lambda: self.update_pid('I', self.i_input.text()))

        i_layout = QHBoxLayout()
        i_layout.addWidget(i_label)
        i_layout.addWidget(self.i_input)
        i_layout.addWidget(i_button)
        control_layout.addLayout(i_layout)

        # Derivative
        d_label = QLabel('Kd:')
        d_label.setStyleSheet(f"font-size: {font_size}px;")
        self.d_input = QLineEdit()
        self.d_input.setStyleSheet(f"font-size: {font_size}px;")
        d_button = QPushButton('Update')
        d_button.setStyleSheet(f"font-size: {font_size}px;")
        d_button.clicked.connect(lambda: self.update_pid('D', self.d_input.text()))

        d_layout = QHBoxLayout()
        d_layout.addWidget(d_label)
        d_layout.addWidget(self.d_input)
        d_layout.addWidget(d_button)
        control_layout.addLayout(d_layout)

        # Sample Time
        sample_time_label = QLabel('Sample Time (ms):')
        sample_time_label.setStyleSheet(f"font-size: {font_size}px;")
        self.sample_time_input = QLineEdit()
        self.sample_time_input.setStyleSheet(f"font-size: {font_size}px;")
        self.sample_time_input.setText(str(pidSampleTime))
        sample_time_button = QPushButton('Update')
        sample_time_button.setStyleSheet(f"font-size: {font_size}px;")
        sample_time_button.clicked.connect(lambda: self.update_sample_time())

        sample_time_layout = QHBoxLayout()
        sample_time_layout.addWidget(sample_time_label)
        sample_time_layout.addWidget(self.sample_time_input)
        sample_time_layout.addWidget(sample_time_button)
        control_layout.addLayout(sample_time_layout)

        # Number of Points to Plot
        points_label = QLabel('Number of Data Points:')
        points_label.setStyleSheet(f"font-size: {font_size}px;")
        self.points_input = QLineEdit(str(num_points))
        self.points_input.setStyleSheet(f"font-size: {font_size}px;")
        points_button = QPushButton('Update')
        points_button.setStyleSheet(f"font-size: {font_size}px;")
        points_button.clicked.connect(self.update_num_points)

        points_layout = QHBoxLayout()
        points_layout.addWidget(points_label)
        points_layout.addWidget(self.points_input)
        points_layout.addWidget(points_button)
        control_layout.addLayout(points_layout)

        # Clear Graph Button
        clear_graph_button = QPushButton('Clear Graph')
        clear_graph_button.setStyleSheet(f"font-size: {font_size}px;")
        clear_graph_button.clicked.connect(self.clear_graph)
        control_layout.addWidget(clear_graph_button)

        # Add spacer
        control_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Enable/Disable PID
        self.enable_button = QPushButton('PID Enabled')
        self.enable_button.setStyleSheet(f"font-size: {font_size}px;")
        self.enable_button.clicked.connect(self.toggle_pid)
        control_layout.addWidget(self.enable_button)

        layout.addLayout(control_layout)

        self.setLayout(layout)

    def initPlot(self):
        global fig, ax, line1, line2
        fig, ax = plt.subplots()
        line1, = ax.plot([], [], 'ro-', label='Actual Voltage', markersize=2, linewidth=1)
        line2, = ax.plot([], [], 'bo-', label='Setpoint', markersize=2, linewidth=1)
        ax.set_xlim(0, num_points)
        ax.set_title('Real-time Arduino Data', fontsize=8)
        ax.set_ylabel('Voltage (V)', fontsize=8)
        ax.set_xlabel('Time (s)', fontsize=8)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.legend(fontsize=6)
        ax.grid(True)

        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)  # Add navigation toolbar

        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.canvas)
        plot_layout.addWidget(self.toolbar)  # Add the toolbar to the layout

        layout = self.layout()
        layout.insertLayout(0, plot_layout, 9)

    def initDataFile(self):
        # Create a new data file with a timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_filename = f"data_log_{timestamp}.txt"
        self.data_file = open(self.data_filename, "w")
        self.data_file.write("Time(s)\tVoltage(V)\tSet Point(V)\tError(%)\n")  # Write headers

    def toggle_pid(self):
        global PIDenabled
        PIDenabled = not PIDenabled
        update_parameters('E', int(PIDenabled))
        self.enable_button.setText('PID Enabled' if PIDenabled else 'PID Disabled')

    def update_num_points(self):
        global num_points
        num_points = int(self.points_input.text())
        ax.set_xlim(0, num_points)
        self.canvas.draw()

    def update_setpoint(self):
        setpoint_value = self.setpoint_input.text()
        update_parameters('S', setpoint_value)
        self.current_setpoint_label.setText(f'Set Point: {setpoint_value}')

    def update_pid(self, param, value):
        update_parameters(param, value)
        if param == 'P':
            self.current_kp_label.setText(f'Kp: {value}')
        elif param == 'I':
            self.current_ki_label.setText(f'Ki: {value}')
        elif param == 'D':
            self.current_kd_label.setText(f'Kd: {value}')

    def update_sample_time(self):
        sample_time_value = self.sample_time_input.text()
        update_parameters('T', sample_time_value)
        self.current_sample_time_label.setText(f'Sample Time: {sample_time_value} ms')

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
    global cnt, arduinoData
    if arduinoData and arduinoData.is_open:
        try:
            if arduinoData.in_waiting > 0:  # Check if there is data available to read
                arduinoString = arduinoData.readline().decode('utf-8').rstrip()  # Read and decode the line of text from the serial port
                print(f"Raw data received: {arduinoString}")  # Debug: Print raw data received
                try:
                    values = arduinoString.split()
                    if len(values) != 2:
                        raise ValueError(f"Expected 2 values, got {len(values)}: {values}")
                    actualVoltage, setpoint = map(float, values)  # Parse the string to get both values

                    # Append data and time
                    Voltage.append(actualVoltage)
                    Setpoint.append(setpoint)
                    current_time = time.time()
                    TimeStamps.append(current_time)

                    # Calculate error
                    error = (actualVoltage - setpoint)/setpoint
                    percentage_error = error * 100
                    Error.append(percentage_error)
                    pid_app.error_label.setText(f'Error: {percentage_error:.2f}%')

                    # Log warning if error exceeds 5%
                    if abs(percentage_error) > 5:
                        pid_app.error_label.setStyleSheet('color: red; font-size: 16px;')
                        print(f"Warning: Error exceeded 5%. Current error: {percentage_error:.2f}%")
                    else:
                        pid_app.error_label.setStyleSheet('color: black; font-size: 16px;')

                    # Save data to file
                    elapsed_time = current_time - TimeStamps[0]  # Time since start
                    pid_app.data_file.write(f"{elapsed_time:.2f}\t{actualVoltage:.4f}\t{setpoint:.4f}\t{percentage_error:.2f}\n")
                    pid_app.data_file.flush()  # Ensure data is written to file immediately

                    # Trim data lists to the specified number of points
                    if len(Voltage) > num_points:
                        Voltage.pop(0)
                        Setpoint.pop(0)
                        TimeStamps.pop(0)
                        Error.pop(0)

                    cnt += 1
                    elapsed_times = [t - TimeStamps[0] for t in TimeStamps]
                    line1.set_data(elapsed_times, Voltage)
                    line2.set_data(elapsed_times, Setpoint)

                    # Adjust y-axis limits dynamically
                    if Voltage and Setpoint:  # Ensure lists are not empty
                        min_voltage = min(min(Voltage), min(Setpoint)) - 0.1
                        max_voltage = max(max(Voltage), max(Setpoint)) + 0.1
                        ax.set_ylim(min_voltage, max_voltage)
                    ax.set_xlim(min(elapsed_times), max(elapsed_times))  # Adjust x-axis dynamically
                    pid_app.canvas.draw()
                    # app.processEvents()  # Ensure GUI updates properly (not needed with canvas.draw())
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

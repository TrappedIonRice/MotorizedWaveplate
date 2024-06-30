import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def update_parameter(ser, command, value):
    ser.write(f"{command}{value}\n".encode())
    time.sleep(0.1)  # Allow some time for the Arduino to process the command

# Function to read and parse data from the serial port
def read_serial_data(ser):
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        if line.startswith("Error:"):
            try:
                error_gap = float(line.split(":")[1].strip())
                return error_gap
            except ValueError:
                pass
    return None

# Function to update the plot
def update_plot(frame, ser, data, line):
    error_gap = read_serial_data(ser)
    if error_gap is not None:
        data.append(error_gap)
        data = data[-100:]  # Keep only the last 100 data points
        line.set_data(range(len(data)), data)
        ax.relim()
        ax.autoscale_view()
    return line,

if __name__ == "__main__":
    ser = None  # Initialize ser to None

    try:
        ser = serial.Serial('COM5', 9600)  # Update 'COM3' to the appropriate port for your Arduino
        time.sleep(2)  # Wait for the serial connection to initialize

        # Update the setpoint and PID parameters
        new_setpoint = 2  # Change to your desired setpoint
        update_parameter(ser, 'S', new_setpoint)

        new_Kp = 3.3 # Change to your desired Kp
        new_Ki = 0.3  # Change to your desired Ki
        new_Kd = 0.00  # Change to your desired Kd
        update_parameter(ser, 'P', new_Kp)
        update_parameter(ser, 'I', new_Ki)
        update_parameter(ser, 'D', new_Kd)

        print("Parameters updated. Reading data...")

        # Initialize plot
        fig, ax = plt.subplots()
        data = []
        line, = ax.plot([], [], lw=2)
        ax.set_ylim(-1, 1)  # Set appropriate y-limits based on expected range of errorGap
        ax.set_xlabel('Time Steps')  # Label for x-axis
        ax.set_ylabel('Error Gap')  # Label for y-axis

        # Set up plot to call update function periodically
        ani = animation.FuncAnimation(fig, update_plot, fargs=(ser, data, line), interval=100)

        plt.show()

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("Exiting due to keyboard interrupt...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if ser is not None and ser.is_open:
            ser.close()

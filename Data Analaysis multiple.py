import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Define the new model function
def model_function(x, a, b, c, d):
    return a * (np.cos(2 * np.pi * x / b - d))**2 + c

def analyse_data(file):
    # Read data from the text file
    # Assuming the file has two columns separated by space
    data = pd.read_csv(file, sep='\s+', header=None)
    data.columns = ['x', 'y']

    # Extract x and y values
    x_data = data['x'].values
    y_data = data['y'].values

    # Fit the model to the data
    initial_guess = [1.6, 600, 0.1, 50]  # Initial guess for the parameters
    params, params_covariance = curve_fit(model_function, x_data, y_data, p0=initial_guess)

    # Extract fitted parameters
    a, b, c, d = params

    # Calculate the fitted y values
    y_fitted = model_function(x_data, a, b, c, d)

    return x_data, y_data, y_fitted


# Example data
x1, y1, fit1 = analyse_data("C:/Users/jacob/physics lab/port test/firstporttest1.txt")
x2, y2, fit2 = analyse_data("C:/Users/jacob/physics lab/port test/firstporttest2.txt")
x3, y3, fit3 = analyse_data("C:/Users/jacob/physics lab/port test/firstporttest3.txt")
x4, y4, fit4 = analyse_data("C:/Users/jacob/physics lab/port test/2nd_port_test_1.txt")
x5, y5, fit5 = analyse_data("C:/Users/jacob/physics lab/port test/2nd_port_test_2.txt")
x6, y6, fit6 = analyse_data("C:/Users/jacob/physics lab/port test/2nd_port_test_3.txt")
x7, y7, fit7 = analyse_data("C:/Users/jacob/physics lab/port test/3rd_port_test_1.txt")
x8, y8, fit8 = analyse_data("C:/Users/jacob/physics lab/port test/3rd_port_test_2.txt")



# Plotting
plt.figure(figsize=(10, 6))

# Data set 1
plt.plot(x1, y1, 'bo', label='Data 1')  # Blue dots
plt.plot(x1, fit1, 'b-', label='Fit 1') # Blue line

# Data set 2
plt.plot(x2, y2, 'ro', label='Data 2')  # Red dots
plt.plot(x2, fit2, 'r-', label='Fit 2') # Red line

# Data set 3
plt.plot(x3, y3, 'go', label='Data 3')  # Green dots
plt.plot(x3, fit3, 'g-', label='Fit 3') # Green line

# Data set 4
plt.plot(x4, y4, 'mo', label='Data 4')  # Magenta dots
plt.plot(x4, fit4, 'm-', label='Fit 4') # Magenta line

# Data set 5
plt.plot(x5, y5, 'co', label='Data 5')  # Cyan dots
plt.plot(x5, fit5, 'c-', label='Fit 5') # Cyan line

# Data set 6
plt.plot(x6, y6, 'yo', label='Data 6')  # Yellow dots
plt.plot(x6, fit6, 'y-', label='Fit 6') # Yellow line

plt.plot(x7, y7, color='orange', label='Data 6')  # Orange dots
plt.plot(x7, fit7, color='orange', label='Fit 6') # Orange line

plt.plot(x8, y8, color='grey', label='Data 6')  # Gray dots
plt.plot(x8, fit8, color='grey', label='Fit 6') # Gray line


# Adding labels and legend
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.title('6 Data Sets with Corresponding Fits')
plt.legend()

# Display the plot
plt.show()


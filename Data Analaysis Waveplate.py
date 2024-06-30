import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Define the new model function
def model_function(x, a, b, c, d):
    return a * (np.cos(2 * np.pi * x / b - d))**2 + c

# Read data from the text file
# Assuming the file has two columns separated by space
data = pd.read_csv("C:/Users/jacob/Downloads/voltage_vs_step.txt", sep='\s+', header=None)
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

# Calculate the mean squared error
mse = np.mean((y_fitted - y_data)**2)

# Calculate the average percent difference
percent_difference = np.abs((y_fitted - y_data) / y_data) * 100
average_percent_difference = np.mean(percent_difference)

# Plot the data and the fitted function
plt.figure(figsize=(10, 6))
plt.plot(x_data, y_data, 'o-', label='Data points')  # 'o-' for line connecting points
plt.plot(x_data, y_fitted, '-', label=f'Fitted function: $y = {a:.2f} (cos(2πx/{b:.2f} - {d:.2f}))^2 + {c:.2f}$')
plt.xlabel('x')
plt.ylabel('y')
plt.legend()
plt.title(f'Fit with MSE: {mse:.4f}, Avg. Percent Difference: {average_percent_difference:.3f}%')
plt.grid(True)
plt.show()

# Print the final function and error
print(f'Final function: y = {a:.4f} (cos(2πx/{b:.4f} - {d:.4f}))^2 + {c:.4f}')
print(f'Mean squared error: {mse:.5f}')
print(f'Average percent difference: {average_percent_difference:.2f}%')

#include "SparkFun_ProDriver_TC78H670FTG_Arduino_Library.h"  // Click here to get the library: http://librarymanager/All#SparkFun_ProDriver
#include <PID_v1.h>

// Hardware Connections and Pin Definitions
const byte motorEnablePin = 7; // Motor enable pin (HIGH: motor on, LOW: motor off)
const int sensorPin = A0; // Input pin for photodetector

// Constants for PID
const double pidSampleTime = 2000; // PID sample time in milliseconds
const double outputLimitMin = -40; // Minimum output limit for PID
const double outputLimitMax = 40; // Maximum output limit for PID
const unsigned long readInterval = 50; // Interval for reading sensor input in milliseconds (adjustable)
const double tolerance = 0.01; // Tolerance for floating-point comparison
const double minStepSize = 0; // Minimum step size required to move the motor

double targetSetpoint = 2; // Target setpoint for PID control (must be within photodiode range)
double currentInput, currentOutput, currentVoltage, errorGap;
int off = 0;

// Define the PID tuning parameters
double Kp = 3, Ki = 0.3, Kd = 0.0;

PRODRIVER myProDriver; // Create instance of the motor driver object
PID myPID(&currentVoltage, &currentOutput, &targetSetpoint, Kp, Ki, Kd, DIRECT); // Specify the links and initial tuning parameters for the PID controller

unsigned long previousMillis = 0; // Stores the last time the sensor was read

void setup() {
  Serial.begin(9600);
  pinMode(motorEnablePin, OUTPUT);

  // Initialize the PID controller with the configured parameters
  setupPID();

  myProDriver.begin(); // Initialize the motor driver with default settings
}

void loop() {
  if (off = 1){
  unsigned long currentMillis = millis();

  updateParameters(); // Check for serial input

  // Measure input and calculate voltage every readInterval milliseconds
  if (currentMillis - previousMillis >= readInterval) {
    previousMillis = currentMillis;

    // Read the sensor input and calculate the corresponding voltage
    currentInput = analogRead(sensorPin);
    currentVoltage = (5.0 / 1023.0) * currentInput;
    
    // Calculate the error gap between the target setpoint and the current voltage
    errorGap = (targetSetpoint - currentVoltage);

    // Check if the error gap is greater than the tolerance and compute PID if true
    if ((abs(errorGap) >= tolerance) && myPID.Compute()) {
      double stepSize = round(50 * abs(currentOutput));

      // Only move the motor if the step size is greater than the minimum step size
      if (stepSize > minStepSize) {
        enableMotor();
        delay(100);
        myProDriver.step(stepSize, getMotorDirection()); // Use output of PID to determine number of steps
        delay(100);
        disableMotor();
      }
    Serial.print("Voltage:");
    Serial.print(currentVoltage);
    Serial.print(" output:");
    Serial.print(currentOutput);
    Serial.print(" stepsize:");
    Serial.print(stepSize);
    Serial.print(" Error:");
    Serial.println(errorGap);

    }
  }
}
}

// Function to enable the motor
void enableMotor() {
  digitalWrite(motorEnablePin, HIGH);
}

// Function to disable the motor
void disableMotor() {
  digitalWrite(motorEnablePin, LOW);
}

// Function to initialize the PID controller
void setupPID() {
  myPID.SetSampleTime(pidSampleTime); // Set the sample time for PID computations
  myPID.SetOutputLimits(outputLimitMin, outputLimitMax); // Set the output limits for the PID controller
  myPID.SetMode(AUTOMATIC); // Set the PID controller to automatic mode
}

// Function to determine motor direction based on the error gap
int getMotorDirection() {
  enableMotor();
  delay(100);
  myProDriver.step(12, 0); // Step the motor in one direction
  
  delay(100);
  // Read the sensor input and calculate the corresponding voltage
  double secondInput = analogRead(sensorPin);
  double secondVoltage = (5.0 / 1023.0) * secondInput;
  double newGap = targetSetpoint - secondVoltage;
  delay(100);
  myProDriver.step(12, 1); // Step the motor in the opposite direction
  delay(100);
  // Determine the direction based on the new gap compared to the error gap
  int direction = (newGap > errorGap) ? 1 : 0;
  // If the PID output is negative, reverse the direction
  if (currentOutput < 0) {
    direction = !direction;
  }
  return direction;
}

void updateParameters() {
  if (Serial.available() > 0) {
    String serialInput = Serial.readStringUntil('\n');
    char command = serialInput.charAt(0);
    double value = serialInput.substring(1).toDouble();
    
    switch (command) {
      case 'S':
        targetSetpoint = value;
        break;
      case 'P':
        Kp = value;
        myPID.SetTunings(Kp, Ki, Kd);
        break;
      case 'I':
        Ki = value;
        myPID.SetTunings(Kp, Ki, Kd);
        break;
      case 'D':
        Kd = value;
        myPID.SetTunings(Kp, Ki, Kd);
        break;
    }
  }
}


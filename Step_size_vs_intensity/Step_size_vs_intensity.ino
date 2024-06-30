#include "SparkFun_ProDriver_TC78H670FTG_Arduino_Library.h" //Click here to get the library: http://librarymanager/All#SparkFun_ProDriver

const byte enable = 7; //EN pin when HIGH and LOW, motor is on and off
int sensorPin = A0; //input to circuit from photodetector
double input, voltage; //Define Variables we'll be connecting to
int start = 0, interval = 20, end = 80, totalstep = 0;
int maxStep = 0;  // Step count at maximum voltage
float maxVoltage = 0;  // Maximum voltage recorded

PRODRIVER myProDriver; //Create instance of this object

void setup()
{
  Serial.begin(9600);
  pinMode(enable, OUTPUT);

  //initialize the variables we're linked to
  input = analogRead(sensorPin);

  myProDriver.begin(); // default settings
}

void loop() {
  // Step forward and record voltage
  for (int stepCount = start; stepCount <= end; stepCount += interval) {
    digitalWrite(enable, HIGH);
    delay(200);
    myProDriver.step(interval);  // move motor
    delay(200);
    digitalWrite(enable, LOW);
    
    delay(300);  // wait for motion to stabilize
    
    input = analogRead(sensorPin);  // read the voltage from photodiode
    float voltage = input * (5.0 / 1023.0);  // convert to voltage

    //Serial.print("Step: ");
    Serial.print(stepCount);
    //Serial.print(", Voltage: ");
    Serial.print(" ");
    Serial.println(voltage);
    totalstep += interval;
    
    // Update maximum voltage and corresponding step count
    if (voltage > maxVoltage) {
      maxVoltage = voltage;
      maxStep = totalstep;
    }
    
    delay(1200);  // wait before next measurement
  }

  // Move back to the step with the maximum voltage
  if (maxStep != 0) {
    int stepsBack = totalstep - maxStep;
    digitalWrite(enable, HIGH);
    delay(200);
    myProDriver.step(stepsBack, 1);  // Move backward to the max voltage step
    delay(200);
    digitalWrite(enable, LOW);
    delay(2000);  // wait for motion to stabilize

    totalstep = maxStep;  // Reset the total step to maxStep after returning to max voltage
  }

  // Move back to the origin
  if (totalstep != 0) {
    digitalWrite(enable, HIGH);
    delay(200);
    myProDriver.step(totalstep, 1);  // Move backward to the origin
    delay(200);
    digitalWrite(enable, LOW);
    delay(2000);  // wait for motion to stabilize

    totalstep = 0;  // Reset step counter after returning to origin
  }

  // Delay before the next loop iteration
  delay(2000);
}

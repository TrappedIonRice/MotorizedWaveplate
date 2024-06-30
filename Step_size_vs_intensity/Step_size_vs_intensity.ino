
//   Hardware Connections:

//   ARDUINO --> PRODRIVER
//   D8 --> STBY
//   D7 --> EN
//   D6 --> MODE0
//   D5 --> MODE1
//   D4 --> MODE2
//   D3 --> MODE3
//   D2 --> ERR

#include "SparkFun_ProDriver_TC78H670FTG_Arduino_Library.h" //Click here to get the library: http://librarymanager/All#SparkFun_ProDriver

const byte enable = 7; //EN pin when HIGH and LOW, motor is on and off
int sensorPin = A0; //input to circuit from photodetector
double input, voltage; //Define Variables we'll be connecting to
int hasrun = 0, start = 0, interval = 20, end = 80, totalstep = 80;


PRODRIVER myProDriver; //Create instance of this object
//Specify the links and initial tuning parameters


void setup()
{
  Serial.begin(9600);
  pinMode(enable, OUTPUT);

  //initialize the variables we're linked to
  input = analogRead(sensorPin);

  myProDriver.begin(); // default settings
}

void loop(){
  
  for (int stepCount = start; stepCount <= end; stepCount += interval) {
    
    digitalWrite(enable, HIGH);
    delay(200);
    myProDriver.step(interval);  // move motor
    delay(200);
    digitalWrite(enable, LOW);
    
    delay(300);  // wait for motion to stabilize
    
    input = analogRead(A0);  // read the voltage from photodiode
    float voltage = input * (5.0 / 1023.0);  // convert to voltage

    //Serial.print("Step: ");
    Serial.print(stepCount);
    //Serial.print(", Voltage: ");
    Serial.print(" ");
    Serial.println(voltage);
    totalstep = totalstep + interval;
    delay(1200);  // wait before next measurement
  }
  int stepsToReturn = totalstep % 1150;
  if (stepsToReturn != 0) {
    digitalWrite(enable, HIGH);
    delay(100);
    myProDriver.step(stepsToReturn, 1);
    delay(200);
    digitalWrite(enable, LOW);
    delay(2000);
    totalstep = 0; // Reset step counter after returning to origin
    delay(2000);
  }
}
  

  

// Pin definitions
const int hallSensorU = 2;  // Hall sensor U
const int hallSensorV = 3;  // Hall sensor V
const int hallSensorW = 18; // Hall sensor W
const int pwmPin = 9;       // PWM pin to control the driver
const int directionPin = 8; // Direction control pin

// Number of pole pairs in the motor
const float  polePairs = 6.8;    // Number of pole pairs in the motor

// Gear ratio
const float gearRatio = 10.3; // Gear ratio

// Desired speed (RPM)
float desiredSpeed = 0; // Desired speed in RPM

// Variables for Hall sensor states
volatile unsigned long lastTime = 0;
volatile unsigned long stateChangeCount = 0;
volatile float currentSpeed = 0;  // Current speed in RPM
volatile float outputSpeed = 0;   // Output speed in RPM
int pwmValue = 0;  // PWM value

// Control variables
float Kp = 0;    // Proportional gain
float Ki = 0;    // Integral gain
float Kd = 0;    // Derivative gain
float previousError = 0;
float integral = 0;

// Direction control
bool direction = true; // true for forward, false for reverse

// Motor running state
bool motorRunning = true; // true if motor is running, false if stopped

void setup() {
  // Set up the pins
  pinMode(hallSensorU, INPUT_PULLUP);
  pinMode(hallSensorV, INPUT_PULLUP);
  pinMode(hallSensorW, INPUT_PULLUP);
  pinMode(pwmPin, OUTPUT);
  pinMode(directionPin, OUTPUT);

  // Attach interrupts to Hall sensors
  attachInterrupt(digitalPinToInterrupt(hallSensorU), hallSensorISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(hallSensorV), hallSensorISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(hallSensorW), hallSensorISR, CHANGE);

  Serial.begin(115200);
}

void loop() {
  // Check for serial input
  if (Serial.available() > 0) {
    String inputString = Serial.readStringUntil('\n');
    if (inputString.startsWith("D")) {
      desiredSpeed = inputString.substring(1).toFloat();
      motorRunning = true;
      Serial.print("Desired Speed set to: ");
      Serial.println(desiredSpeed);
    } else if (inputString.startsWith("R")) {
      direction = false;
      Serial.println("Direction set to reverse");
    } else if (inputString.startsWith("F")) {
      direction = true;
      Serial.println("Direction set to forward");
    } else if (inputString.startsWith("S")) {
      motorRunning = false;
      analogWrite(pwmPin, 0); // Stop the motor by setting PWM to 0
      Serial.println("Motor stopped");
    } else if (inputString.startsWith("KP")) {
      Kp = inputString.substring(2).toFloat();
      Serial.print("Kp set to: ");
      Serial.println(Kp);
    } else if (inputString.startsWith("KI")) {
      Ki = inputString.substring(2).toFloat();
      Serial.print("Ki set to: ");
      Serial.println(Ki);
    } else if (inputString.startsWith("KD")) {
      Kd = inputString.substring(2).toFloat();
      Serial.print("Kd set to: ");
      Serial.println(Kd);
    }
  }

  if (motorRunning) {
    // Set direction pin based on direction
    digitalWrite(directionPin, direction ? HIGH : LOW);

    // Calculate speed based on Hall sensor state changes
    unsigned long currentTime = millis();
    static unsigned long lastSpeedCalcTime = 0;
    if (currentTime - lastSpeedCalcTime >= 1000) { // Update every second
      noInterrupts(); // Disable interrupts during calculation for safety
      currentSpeed = (stateChangeCount / (6.0 * polePairs)) * (60000.0 / (currentTime - lastSpeedCalcTime)); // Speed in RPM
      stateChangeCount = 0; // Reset count
      lastSpeedCalcTime = currentTime;
      interrupts(); // Re-enable interrupts

      // Calculate output speed
      outputSpeed = currentSpeed / gearRatio;

      // Calculate the error
      float error = desiredSpeed - outputSpeed;

      // Update integral
      integral += error;

      // Calculate derivative
      float derivative = error - previousError;

      // Calculate PID control output
      pwmValue = Kp * error + Ki * integral + Kd * derivative;

      // Constrain PWM value to be between 0 and 255
      pwmValue = constrain(pwmValue, 0, 255);

      analogWrite(pwmPin, pwmValue); // Output the PWM signal

      // Update previous error
      previousError = error;

      // Debug output
      Serial.print("Current Speed: ");
      Serial.print(currentSpeed);
      Serial.print(" RPM, Output Speed: ");
      Serial.print(outputSpeed);
      Serial.print(" RPM, PWM Value: ");
      Serial.print(pwmValue);
      Serial.print(", Error: ");
      Serial.println(error);
    }
  }
}

// ISR for Hall sensors
void hallSensorISR() {
  static int lastHallState = -1; // -1 indicates uninitialized state
  int hallUState = digitalRead(hallSensorU);
  int hallVState = digitalRead(hallSensorV);
  int hallWState = digitalRead(hallSensorW);
  int newHallState = (hallUState << 2) | (hallVState << 1) | hallWState;

  // Only count valid state changes (001, 010, 011, 100, 101, 110)
  switch (newHallState) {
    case 0b010:
    case 0b011:
    case 0b001:
    case 0b101:
    case 0b100:
    case 0b110:
      if (newHallState != lastHallState) {
        stateChangeCount++;
        lastHallState = newHallState;
      }
      break;
    default:
      // Invalid state, do nothing
      break;
  }
}

const int MOTOR_COUNT = 9;
const int motorPins[MOTOR_COUNT][2] = {
  {2, 3}, {4, 5}, {6, 7}, {8, 9}, {10, 11}, {12, 13}, {A0, A1}, {A2, A3}, {A4, A5}
};

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < MOTOR_COUNT; i++) {
    pinMode(motorPins[i][0], OUTPUT);
    pinMode(motorPins[i][1], OUTPUT);
    stopMotor(i);
  }
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command.startsWith("DISPENSE:")) {
    int first = command.indexOf(':');
    int second = command.indexOf(':', first + 1);
    int slot = command.substring(first + 1, second).toInt();
    int turns = command.substring(second + 1).toInt();
    dispense(slot - 1, turns);
  }
}

void dispense(int motorIndex, int turns) {
  if (motorIndex < 0 || motorIndex >= MOTOR_COUNT || turns <= 0) {
    Serial.println("ERR:BAD_COMMAND");
    return;
  }

  for (int i = 0; i < turns; i++) {
    rotateMotor(motorIndex, 900);
    delay(250);
  }
  stopMotor(motorIndex);
  Serial.println("OK:DISPENSED");
}

void rotateMotor(int motorIndex, int durationMs) {
  digitalWrite(motorPins[motorIndex][0], HIGH);
  digitalWrite(motorPins[motorIndex][1], LOW);
  delay(durationMs);
}

void stopMotor(int motorIndex) {
  digitalWrite(motorPins[motorIndex][0], LOW);
  digitalWrite(motorPins[motorIndex][1], LOW);
}

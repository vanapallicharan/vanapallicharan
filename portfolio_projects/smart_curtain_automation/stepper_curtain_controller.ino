#include <Stepper.h>

const int STEPS_PER_REV = 200;
const int OPEN_LIMIT_PIN = 7;
const int CLOSE_LIMIT_PIN = 8;

Stepper curtainMotor(STEPS_PER_REV, 2, 3, 4, 5);

void setup() {
  Serial.begin(9600);
  pinMode(OPEN_LIMIT_PIN, INPUT_PULLUP);
  pinMode(CLOSE_LIMIT_PIN, INPUT_PULLUP);
  curtainMotor.setSpeed(60);
  Serial.println("Curtain automation ready: send OPEN, CLOSE, or STOP");
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();

  if (command == "OPEN") {
    moveCurtain(true);
  } else if (command == "CLOSE") {
    moveCurtain(false);
  } else if (command == "STOP") {
    Serial.println("STOPPED");
  }
}

void moveCurtain(bool opening) {
  int limitPin = opening ? OPEN_LIMIT_PIN : CLOSE_LIMIT_PIN;
  int direction = opening ? 1 : -1;
  int maxSteps = STEPS_PER_REV * 8;

  for (int stepCount = 0; stepCount < maxSteps; stepCount++) {
    if (digitalRead(limitPin) == LOW) {
      Serial.println(opening ? "OPEN_LIMIT_REACHED" : "CLOSE_LIMIT_REACHED");
      return;
    }
    curtainMotor.step(direction);
  }

  Serial.println(opening ? "OPEN_COMPLETE_ESTIMATED" : "CLOSE_COMPLETE_ESTIMATED");
}

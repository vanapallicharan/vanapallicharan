#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 5
#define RST_PIN 22
#define RELAY_PIN 26
#define BUTTON_PIN 27

MFRC522 rfid(SS_PIN, RST_PIN);

String allowedCards[] = {
  "A1 B2 C3 D4",
  "11 22 33 44"
};

void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  lockDoor();
  Serial.println("Smart magnetic door lock ready");
}

void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    unlockDoor("push-button");
  }

  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "REMOTE_UNLOCK") {
      unlockDoor("remote-dashboard");
    }
  }

  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  String uid = readUid();
  if (isAllowed(uid)) {
    unlockDoor("rfid:" + uid);
  } else {
    Serial.println("ACCESS_DENIED:" + uid);
  }
  rfid.PICC_HaltA();
}

String readUid() {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
    if (i + 1 < rfid.uid.size) uid += " ";
  }
  uid.toUpperCase();
  return uid;
}

bool isAllowed(String uid) {
  for (String card : allowedCards) {
    if (uid == card) {
      return true;
    }
  }
  return false;
}

void unlockDoor(String source) {
  Serial.println("UNLOCK:" + source);
  digitalWrite(RELAY_PIN, HIGH);
  delay(5000);
  lockDoor();
}

void lockDoor() {
  digitalWrite(RELAY_PIN, LOW);
}

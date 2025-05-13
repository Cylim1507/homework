#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>

#define RST_PIN         9          // Configurable, see your wiring
#define SS_PIN          10         // Configurable, see your wiring
#define BUZZER_PIN      3          // Pin connected to the buzzer
#define SERVO_PIN       5          // Servo motor pin

MFRC522 mfrc522(SS_PIN, RST_PIN);
Servo servo;

String MASTER_UID = "73 C9 2D 20";  // Replace with your actual master UID
bool isLocked = true;

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();
  servo.attach(SERVO_PIN);
  pinMode(BUZZER_PIN, OUTPUT);
  servo.write(70);  // Initial lock position
  delay(1000);
  Serial.println("System ready. Scan RFID tag...");
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial())
    return;

  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i], HEX);
    if (i < mfrc522.uid.size - 1)
      uid += " ";
  }
  uid.toUpperCase();

  String status;
  if (uid == MASTER_UID) {
    isLocked = !isLocked;
    status = isLocked ? "LOCKED" : "UNLOCKED";
    servo.write(isLocked ? 70 : 160);

    // ✅ Success: turn buzzer ON for 0.5 second
    digitalWrite(BUZZER_PIN, HIGH);
    delay(500);
    digitalWrite(BUZZER_PIN, LOW);
  } else {
    status = "DENIED";

    // ❌ Failure: buzzer ON and OFF twice (0.5s each)
    for (int i = 0; i < 2; i++) {
      digitalWrite(BUZZER_PIN, HIGH);
      delay(500);
      digitalWrite(BUZZER_PIN, LOW);
      delay(250);  // pause between buzzes
    }
  }

  Serial.print("LOG:");
  Serial.print(uid);
  Serial.print(",");
  Serial.println(status);

  mfrc522.PICC_HaltA();
  delay(1000);  // small delay to prevent rapid re-scanning
}

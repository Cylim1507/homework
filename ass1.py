#include <Servo.h>
#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <MFRC522.h>

// Pins
#define SS_PIN 10
#define RST_PIN 9
#define FSR_PIN A0
#define BUZZER_PIN 2

// Time tracking
unsigned long startTime;
const unsigned long scanInterval = 500;
unsigned long lastScanTime = 0;
unsigned long unlockTime = 0;

// UID setup
String AUTHORIZED_UIDS[] = { " 73 05 E8 A0", " 14 AF 43 D9" };
const int NUM_AUTHORIZED_UIDS = sizeof(AUTHORIZED_UIDS) / sizeof(AUTHORIZED_UIDS[0]);

// Components
Servo servo;
MFRC522 rfid(SS_PIN, RST_PIN);

// States
bool isLocked = true;
int forceThreshold = 100;
int failedScanCount = 0;
const int maxFailedScans = 3;

bool waitingForItem = false;
bool alertTriggered = false;
bool continuousAlert = false;

void softReset() {
  asm volatile("jmp 0");
}

void setup() {
  Serial.begin(9600);
  servo.attach(3);
  servo.write(70); // Locked position
  pinMode(BUZZER_PIN, OUTPUT);
  SPI.begin();
  rfid.PCD_Init();
  startTime = millis();
}

void loop() {
  int fsrReading = analogRead(FSR_PIN);

  // 🔔 Buzzer if locked and no item present (security mode)
  if (isLocked && fsrReading < forceThreshold) {
    tone(BUZZER_PIN, 1000);
    delay(500);
    noTone(BUZZER_PIN);
    delay(500);
  }

  // 🕒 Scan RFID card
  if (millis() - lastScanTime >= scanInterval) {
    lastScanTime = millis();

    if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
      String uid = "";
      for (byte i = 0; i < rfid.uid.size; i++) {
        uid += (rfid.uid.uidByte[i] < 0x10 ? " 0" : " ");
        uid += String(rfid.uid.uidByte[i], HEX);
      }
      uid.toUpperCase();

      Serial.print("Scanned UID: ");
      Serial.println(uid);

      String status = "";
      bool isAuthorized = false;

      for (int i = 0; i < NUM_AUTHORIZED_UIDS; i++) {
        if (uid == AUTHORIZED_UIDS[i]) {
          isAuthorized = true;
          break;
        }
      }

      if (isAuthorized) {
        isLocked = !isLocked;
        status = isLocked ? "LOCKED" : "UNLOCKED";
        servo.write(isLocked ? 70 : 160);
        failedScanCount = 0;

        if (!isLocked) {
          unlockTime = millis();
          waitingForItem = true;
          alertTriggered = false;
          Serial.println("🔓 Door unlocked — waiting for item placement");
        } else {
          waitingForItem = false;
          alertTriggered = false;
        }

        // ✅ Success beep
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);
      } else {
        status = "DENIED";
        failedScanCount++;

        // ❌ Denied buzzer
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);
        delay(100);
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);

        if (failedScanCount >= maxFailedScans) {
          Serial.println("Too many failed scans. Resetting...");
          delay(1000);
          softReset();
        }
      }

      // Log to Python
      Serial.print("LOG:");
      Serial.print(uid);
      Serial.print(",");
      Serial.print(status);
      Serial.print(",");

      // Fake clock
      unsigned long elapsedMillis = millis() - startTime;
      unsigned long totalSeconds = elapsedMillis / 1000;
      int seconds = totalSeconds % 60;
      int minutes = (totalSeconds / 60) % 60;
      int hours = (totalSeconds / 3600) % 24;

      if (hours < 10) Serial.print("0");
      Serial.print(hours); Serial.print(":");
      if (minutes < 10) Serial.print("0");
      Serial.print(minutes); Serial.print(":");
      if (seconds < 10) Serial.print("0");
      Serial.println(seconds);

      delay(1000);
      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
    }
  }

  // 🕒 After UNLOCK — 15 sec delay alert logic
  if (!isLocked && waitingForItem) {
    if (millis() - unlockTime >= 15000) {
      if (fsrReading < forceThreshold) {
        if (!alertTriggered) {
          Serial.println("⏰ No item detected after 15s of UNLOCK — start alert");
          alertTriggered = true;
        }
        tone(BUZZER_PIN, 1000);  // Continuous buzzer
      } else {
        noTone(BUZZER_PIN);
        waitingForItem = false;
        alertTriggered = false;
        Serial.println("✅ Item returned after unlock delay — stop alert");
      }
    }
  }

  // 🔁 Handle serial commands from Python
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'F') {
      continuousAlert = true;
    } else if (cmd == 'S') {
      continuousAlert = false;
      noTone(BUZZER_PIN);
    }
  }

  if (continuousAlert) {
    if (fsrReading < forceThreshold) {
      tone(BUZZER_PIN, 1000);
    } else {
      noTone(BUZZER_PIN);
      continuousAlert = false;
    }
  }
}

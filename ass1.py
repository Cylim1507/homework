#include <Servo.h>
#include <SPI.h>
#include <MFRC522.h>

// Pins
#define SS_PIN 10
#define RST_PIN 9
#define FSR_PIN A0
#define BUZZER_PIN 2

// Authorized UIDs
String AUTHORIZED_UIDS[] = { " 73 05 E8 A0", " 14 AF 43 D9" };
const int NUM_AUTHORIZED_UIDS = sizeof(AUTHORIZED_UIDS) / sizeof(AUTHORIZED_UIDS[0]);

// State
bool isLocked = true;
unsigned long lastScanTime = 0;
const unsigned long scanInterval = 500;
int forceThreshold = 100;

int failedScanCount = 0;
const int maxFailedScans = 3;

unsigned long unlockTime = 0;
bool waitingForItem = false;
bool continuousAlert = false;  // Python alert

// Components
Servo servo;
MFRC522 rfid(SS_PIN, RST_PIN);

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
}

void loop() {
  int fsrReading = analogRead(FSR_PIN);

  // --- Serial Commands from Python ---
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'F') {
      continuousAlert = true;
    } else if (cmd == 'S') {
      continuousAlert = false;
      noTone(BUZZER_PIN);
    }
  }

  // --- Continuous Alert from Python ---
  if (continuousAlert) {
    if (fsrReading < forceThreshold) {
      tone(BUZZER_PIN, 1000);
    } else {
      noTone(BUZZER_PIN);
      continuousAlert = false;
    }
  }

  // --- FSR Alert While Locked ---
  if (isLocked && fsrReading < forceThreshold) {
    tone(BUZZER_PIN, 1000);
    delay(500);
    noTone(BUZZER_PIN);
    delay(500);
  }

  // --- RFID Scan ---
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
        }

        // ✅ Single beep
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);
      } else {
        status = "DENIED";
        failedScanCount++;

        // ❌ Double beep
        for (int i = 0; i < 2; i++) {
          digitalWrite(BUZZER_PIN, HIGH);
          delay(100);
          digitalWrite(BUZZER_PIN, LOW);
          delay(100);
        }

        if (failedScanCount >= maxFailedScans) {
          Serial.println("Too many failed scans. Resetting...");
          delay(1000);
          softReset();
        }
      }

      // Send to Python
      Serial.print("LOG:");
      Serial.print(uid);
      Serial.print(",");
      Serial.println(status);

      delay(1000);
      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
    }
  }

  // --- Continuous Buzzer After Unlock Timeout ---
  if (!isLocked && waitingForItem) {
    if (millis() - unlockTime >= 15000) {
      if (fsrReading < forceThreshold) {
        tone(BUZZER_PIN, 1000);  // Continuous beep
      } else {
        noTone(BUZZER_PIN);
        waitingForItem = false; // Item is back
      }
    }
  }

  // --- Reset if locked again ---
  if (isLocked) {
    waitingForItem = false;
  }
}

#include <Servo.h>
#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <MFRC522.h>

// Pins
#define SS_PIN 10
#define RST_PIN 9
#define FSR_PIN A0
#define BUZZER_PIN 2

// Authorized UIDs
String AUTHORIZED_UIDS[] = { " 73 05 E8 A0", " 14 AF 43 D9" };  // Add more as needed
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
bool continuousAlert = false;  // Alert from Python

// Components
Servo servo;
MFRC522 rfid(SS_PIN, RST_PIN);

void softReset() {
  asm volatile("jmp 0");
}

void setup() {
  Serial.begin(9600);
  servo.attach(3);
  servo.write(70); // Locked
  pinMode(BUZZER_PIN, OUTPUT);
  SPI.begin();
  rfid.PCD_Init();
}

void loop() {
  int fsrReading = analogRead(FSR_PIN);

  // --- Handle Serial Commands from Python ---
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'F') {
      continuousAlert = true;
    } else if (cmd == 'S') {
      continuousAlert = false;
      noTone(BUZZER_PIN);
    }
  }

  // --- Python Alert Logic ---
  if (continuousAlert) {
    if (fsrReading < forceThreshold) {
      tone(BUZZER_PIN, 1000);  // Keep buzzing
    } else {
      noTone(BUZZER_PIN);
      continuousAlert = false;
    }
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

        // ✅ Success beep
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

      // Log to Python
      Serial.print("LOG:");
      Serial.print(uid);
      Serial.print(",");
      Serial.println(status);

      delay(1000);
      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
    }
  }

  // --- After Unlock: Wait 15s then check if item is returned ---
  if (!isLocked && waitingForItem) {
    if (millis() - unlockTime >= 15000) {
      if (fsrReading < forceThreshold) {
        tone(BUZZER_PIN, 1000);  // Buzzer ON
      } else {
        noTone(BUZZER_PIN);      // Item is placed back
        waitingForItem = false;
      }
    }
  }

  // --- If relocked, reset everything ---
  if (isLocked) {
    noTone(BUZZER_PIN);
    waitingForItem = false;
  }
}

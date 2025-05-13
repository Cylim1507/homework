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
const unsigned long millisPerSecond = 1000;
const unsigned long millisPerMinute = millisPerSecond * 60;
const unsigned long millisPerHour = millisPerMinute * 60;

// Authorized UIDs
String AUTHORIZED_UIDS[] = { " 73 05 E8 A0", " 14 AF 43 D9" }; // Add more if needed
const int NUM_AUTHORIZED_UIDS = sizeof(AUTHORIZED_UIDS) / sizeof(AUTHORIZED_UIDS[0]);

// Settings
bool isLocked = true;
unsigned long lastScanTime = 0;
const unsigned long scanInterval = 500;
int forceThreshold = 100;
int startHour = 17;
int startMinute = 0;
int startSecond = 0;
int failedScanCount = 0;
const int maxFailedScans = 3;

// Components
Servo servo;
// LiquidCrystal_I2C lcd(0x27, 16, 2); // Optional
MFRC522 rfid(SS_PIN, RST_PIN);

void softReset() {
  asm volatile("jmp 0");
}

void setup() {
  Serial.begin(9600);
  // lcd.init();
  // lcd.backlight();
  servo.attach(3);
  servo.write(70); // Locked position
  pinMode(BUZZER_PIN, OUTPUT);
  SPI.begin();
  rfid.PCD_Init();
  startTime = millis(); // record boot time

  // lcd.setCursor(4, 0); lcd.print("Welcome!");
  // lcd.setCursor(1, 1); lcd.print("Put your card");
}

void loop() {
  int fsrReading = analogRead(FSR_PIN);

  // Buzzer alert if locked and no pressure
  if (isLocked && fsrReading < forceThreshold) {
    tone(BUZZER_PIN, 1000);
    delay(500);
    noTone(BUZZER_PIN);
    delay(500);
  }

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

        // ✅ Success Buzzer ON for 0.5 sec
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);
      } else {
        status = "DENIED";
        failedScanCount++;

        // ❌ Invalid Buzzer ON twice for 0.5s each
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

      // Log time
      Serial.print("LOG:");
      Serial.print(uid);
      Serial.print(",");
      Serial.print(status);
      Serial.print(",");

      unsigned long elapsedMillis = millis() - startTime;
      unsigned long totalSeconds = elapsedMillis / 1000;
      int seconds = (startSecond + totalSeconds) % 60;
      int minutes = (startMinute + (startSecond + totalSeconds) / 60) % 60;
      int hours = (startHour + (startMinute + (startSecond + totalSeconds) / 60) / 60) % 24;

      Serial.print("Current Time: ");
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

  // Show welcome again (LCD optional)
  if (millis() - lastScanTime >= 2000) {
    // lcd.setCursor(4, 0); lcd.print("Welcome!");
    // lcd.setCursor(1, 1); lcd.print("Put your card");
  }
}

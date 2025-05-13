#include <Servo.h>
#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <MFRC522.h>

// Pins
#define SS_PIN 10
#define RST_PIN 9
#define FSR_PIN A0
#define BUZZER_PIN 2
unsigned long startTime;
const unsigned long millisPerSecond = 1000;
const unsigned long millisPerMinute = millisPerSecond * 60;
const unsigned long millisPerHour = millisPerMinute * 60;

// Settings
String MASTER_UID = " 73 05 E8 A0"; // UID format: " XX XX XX XX"
bool isLocked = true;
unsigned long lastScanTime = 0;
const unsigned long scanInterval = 500;
int forceThreshold = 100;
int startHour = 17;
int startMinute = 0;
int startSecond = 0;

// Components
Servo servo;
// LiquidCrystal_I2C lcd(0x27, 16, 2); // Commented out
MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);
  // lcd.init();
  // lcd.backlight();
  servo.attach(3);
  servo.write(70); // Locked position
  pinMode(BUZZER_PIN, OUTPUT);
  SPI.begin();
  rfid.PCD_Init();
  startTime = millis(); // capture boot time

  // lcd.setCursor(4, 0);
  // lcd.print("Welcome!");
  // lcd.setCursor(1, 1);
  // lcd.print("Put your card");
}

void loop() {
  int fsrReading = analogRead(FSR_PIN);
  if (isLocked && fsrReading < forceThreshold) {
    digitalWrite(BUZZER_PIN, HIGH);
    // lcd.clear();
    // lcd.print("ALERT: No object!");
    delay(500);
    digitalWrite(BUZZER_PIN, LOW);
  }

  if (millis() - lastScanTime >= scanInterval) {
    lastScanTime = millis();
    if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
      // lcd.clear();
      // lcd.setCursor(0, 0);
      // lcd.print("Scanning...");

      String uid = "";
      for (byte i = 0; i < rfid.uid.size; i++) {
        uid += (rfid.uid.uidByte[i] < 0x10 ? " 0" : " ");
        uid += String(rfid.uid.uidByte[i], HEX);
      }
      uid.toUpperCase();

      Serial.print("Scanned UID: ");
      Serial.println(uid);

      String status = "";
      if (uid == MASTER_UID) {
        isLocked = !isLocked;
        status = isLocked ? "LOCKED" : "UNLOCKED";
        servo.write(isLocked ? 70 : 160);
        // lcd.clear();
        // lcd.print(isLocked ? "Door locked" : "Door unlocked");
      } else {
        status = "DENIED";
        // lcd.clear();
        // lcd.print("Wrong card!");
      }

      Serial.print("LOG:");
      Serial.print(uid);
      Serial.print(",");
      Serial.print(status);
      Serial.print(",");

      unsigned long currentMillis = millis();
      unsigned long elapsedMillis = currentMillis - startTime;

      // Calculate time offset
      unsigned long totalSeconds = elapsedMillis / 1000;
      int seconds = (startSecond + totalSeconds) % 60;
      int minutes = (startMinute + (startSecond + totalSeconds) / 60) % 60;
      int hours = (startHour + (startMinute + (startSecond + totalSeconds) / 60) / 60) % 24;

      // Print time
      Serial.print("Current Time: ");
      if (hours < 10) Serial.print("0");
      Serial.print(hours);
      Serial.print(":");
      if (minutes < 10) Serial.print("0");
      Serial.print(minutes);
      Serial.print(":");
      if (seconds < 10) Serial.print("0");
      Serial.println(seconds);

      delay(1000);
      rfid.PICC_HaltA();
    }
  }

  if (millis() - lastScanTime >= 2000) {
    // lcd.setCursor(4, 0);
    // lcd.print("Welcome!");
    // lcd.setCursor(1, 1);
    // lcd.print("Put your card");
  }

  // 🔄 Handle serial commands from Python
  if (Serial.available()) {
    char command = Serial.read();
    if (command == 'S') {
      digitalWrite(BUZZER_PIN, HIGH);
      delay(500);
      digitalWrite(BUZZER_PIN, LOW);
    } else if (command == 'F') {
      digitalWrite(BUZZER_PIN, HIGH);
      delay(500);
      digitalWrite(BUZZER_PIN, LOW);
      delay(200);
      digitalWrite(BUZZER_PIN, HIGH);
      delay(500);
      digitalWrite(BUZZER_PIN, LOW);
    }
  }
}

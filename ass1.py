import pymysql
import serial
from datetime import datetime
import time
import RPi.GPIO as GPIO
import spidev

# --- Configuration ---
DB_HOST = "localhost"
DB_USER = "kali"
DB_PASSWORD = ""
DB_NAME = "assignment1"

SERIAL_PORT = '/dev/ttyS0'  # or '/dev/ttyACM0'
BAUD_RATE = 9600

BUZZER_PIN = 2
FSR_CHANNEL = 0  # MCP3008 channel where FSR is connected
FSR_THRESHOLD = 100

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# --- SPI Setup for MCP3008 ---
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel):
    if not 0 <= channel <= 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((adc[1] & 3) << 8) + adc[2]
    return value

# --- Buzzer Functions ---
def buzzer_success():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def buzzer_error():
    for _ in range(2):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.2)

# --- Database logging function ---
def log_to_db(uid, status):
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        with connection.cursor() as cursor:
            sql = "INSERT INTO logs (uid, status, timestamp) VALUES (%s, %s, %s)"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(sql, (uid, status, timestamp))
        connection.commit()
        print(f"✅ Logged: UID={uid}, STATUS={status}, TIME={timestamp}")
    except pymysql.MySQLError as e:
        print(f"❌ MySQL Error: {e}")
    finally:
        if connection:
            connection.close()

# --- Main loop ---
def main():
    try:
        print("🔌 Connecting to serial...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.setDTR(False)
        time.sleep(1)
        ser.flushInput()
        ser.setDTR(True)
        time.sleep(2)
        print("📡 Listening for RFID scans...")

        while True:
            # --- Force Sensor Check ---
            fsr_value = read_adc(FSR_CHANNEL)
            if fsr_value < FSR_THRESHOLD:
                print("⚠️ FSR alert: Object not detected!")
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(BUZZER_PIN, GPIO.LOW)

            # --- RFID Check ---
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("LOG:"):
                try:
                    parts = line.split(",")
                    uid = parts[0][4:].strip()
                    status = parts[1].strip()

                    log_to_db(uid, status)

                    if status == "UNLOCKED" or status == "LOCKED":
                        buzzer_success()
                    elif status == "DENIED":
                        buzzer_error()
                except Exception as e:
                    print(f"⚠️ Failed to parse line: {line} → {e}")

    except KeyboardInterrupt:
        print("\n🛑 Program terminated by user.")
    finally:
        GPIO.cleanup()
        spi.close()

if __name__ == "__main__":
    main()

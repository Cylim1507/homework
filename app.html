import serial
import datetime
import csv
from time import sleep, time
from threading import Timer

# Configuration
SERIAL_PORT = '/dev/ttyS0'  # Change to your Arduino's serial port
BAUD_RATE = 9600
LOG_FILE = 'rfid_access_log.csv'
ALARM_DELAY = 15  # seconds to wait before triggering alarm when empty while unlocked

class RFIDMonitor:
    def __init__(self):
        self.ser = None
        self.last_unlock_time = None
        self.empty_since_unlock = False
        self.alarm_timer = None
        self.current_status = "LOCKED"
        self.fsr_state = "UNKNOWN"

    def setup_serial_connection(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            sleep(2)
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {SERIAL_PORT}: {e}")
            return False

    def log_access(self, uid, status, timestamp):
        with open(LOG_FILE, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if csvfile.tell() == 0:
                writer.writerow(['Timestamp', 'UID', 'Status'])
            writer.writerow([timestamp, uid.strip(), status])

    def trigger_alarm(self):
        print("ALARM: Unlocked and empty for 15 seconds!")
        if self.ser and self.ser.is_open:
            self.ser.write(b'ALARM\n')
        self.log_access("SYSTEM", "ALARM_TRIGGERED",
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def start_alarm_timer(self):
        if self.alarm_timer:
            self.alarm_timer.cancel()
        self.alarm_timer = Timer(ALARM_DELAY, self.trigger_alarm)
        self.alarm_timer.start()

    def cancel_alarm_timer(self):
        if self.alarm_timer:
            self.alarm_timer.cancel()
            self.alarm_timer = None

    def process_serial_line(self, line):
        if line.startswith("Scanned UID:"):
            current_uid = line.replace("Scanned UID:", "").strip()
            print(f"Card scanned: {current_uid}")

        elif line.startswith("LOG:"):
            parts = line.split(",")
            if len(parts) >= 2:
                uid = parts[0].replace("LOG:", "").strip()
                status = parts[1].strip()
                
                self.current_status = status

                if "UNLOCKED" in status:
                    self.last_unlock_time = time()
                    self.cancel_alarm_timer()
                elif "LOCKED" in status:
                    self.cancel_alarm_timer()

                log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{log_time} - {uid} - {status}")
                self.log_access(uid, status, log_time)

        elif line.startswith("FSR:"):
            fsr_value = int(line.replace("FSR:", "").strip())
            self.fsr_state = "EMPTY" if fsr_value < 100 else "OCCUPIED"

            if (self.current_status == "UNLOCKED" and
                self.fsr_state == "EMPTY" and
                not self.alarm_timer):
                self.start_alarm_timer()
            elif self.fsr_state == "OCCUPIED":
                self.cancel_alarm_timer()

        elif line:
            print(line)

    def monitor_serial(self):
        print("Monitoring serial port... Press Ctrl+C to exit")
        try:
            while True:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    self.process_serial_line(line)
                sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.cancel_alarm_timer()
            if self.ser and self.ser.is_open:
                self.ser.close()

    def main(self):
        if self.setup_serial_connection():
            self.monitor_serial()

if __name__ == "__main__":
    monitor = RFIDMonitor()
    monitor.main()

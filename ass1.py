import serial
import datetime
import csv
from time import sleep, time
from threading import Timer

# Configuration
SERIAL_PORT = 'COM3'  # Change to your Arduino's serial port
BAUD_RATE = 9600
LOG_FILE = 'rfid_access_log.csv'
ALARM_DELAY = 15  # seconds to wait before triggering alarm when empty while unlocked

class RFIDMonitor:
    def __init__(self):
        self.ser = None
        self.last_unlock_time = None
        self.empty_since_unlock = False
        self.alarm_timer = None
        self.current_status = "LOCKED"  # Track current lock status
        self.fsr_state = "UNKNOWN"  # Track force sensor state

    def setup_serial_connection(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            sleep(2)  # Wait for connection to establish
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
            self.ser.write(b'ALARM\n')  # Send alarm command to Arduino
        # Log this alarm event
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
            if len(parts) >= 3:
                uid = parts[0].replace("LOG:", "").strip()
                status = parts[1].strip()
                timestamp = parts[2].replace("Current Time: ", "").strip()
                
                # Update current status
                self.current_status = status
                
                # Record unlock time
                if "UNLOCKED" in status:
                    self.last_unlock_time = time()
                    self.cancel_alarm_timer()
                elif "LOCKED" in status:
                    self.cancel_alarm_timer()
                
                # Log the access
                log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{log_time} - {uid} - {status} - Device Time: {timestamp}")
                self.log_access(uid, status, log_time)
        
        elif line.startswith("FSR:"):
            # Example format: "FSR: 245" or "FSR: 0" (empty)
            fsr_value = int(line.replace("FSR:", "").strip())
            self.fsr_state = "EMPTY" if fsr_value < 100 else "OCCUPIED"
            
            # Check for alarm condition
            if (self.current_status == "UNLOCKED" and 
                self.fsr_state == "EMPTY" and 
                not self.alarm_timer):
                self.start_alarm_timer()
            elif self.fsr_state == "OCCUPIED":
                self.cancel_alarm_timer()
        
        elif line:  # Only print non-empty lines
            print(line)

    def monitor_serial(self):
        print("Monitoring serial port... Press Ctrl+C to exit")
        try:
            while True:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    self.process_serial_line(line)
                sleep(0.1)  # Small delay to prevent CPU overuse
        
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

import serial
import datetime
import csv
from time import sleep

# Configuration
SERIAL_PORT = 'COM3'  # Change to your Arduino's serial port
BAUD_RATE = 9600
LOG_FILE = 'rfid_access_log.csv'

def setup_serial_connection():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        sleep(2)  # Wait for connection to establish
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
        return ser
    except serial.SerialException as e:
        print(f"Failed to connect to {SERIAL_PORT}: {e}")
        return None

def log_access(uid, status, timestamp):
    with open(LOG_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header if file is empty
        if csvfile.tell() == 0:
            writer.writerow(['Timestamp', 'UID', 'Status'])
        writer.writerow([timestamp, uid.strip(), status])

def monitor_serial(ser):
    print("Monitoring serial port... Press Ctrl+C to exit")
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                # Parse the Arduino's output
                if line.startswith("Scanned UID:"):
                    current_uid = line.replace("Scanned UID:", "").strip()
                    print(f"Card scanned: {current_uid}")
                
                elif line.startswith("LOG:"):
                    parts = line.split(",")
                    if len(parts) >= 3:
                        uid = parts[0].replace("LOG:", "").strip()
                        status = parts[1].strip()
                        timestamp = parts[2].replace("Current Time: ", "").strip()
                        
                        # Get current system time for logging
                        log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"{log_time} - {uid} - {status} - Device Time: {timestamp}")
                        log_access(uid, status, log_time)
                
                else:
                    if line:  # Only print non-empty lines
                        print(line)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if ser.is_open:
            ser.close()

def main():
    ser = setup_serial_connection()
    if ser:
        monitor_serial(ser)

if __name__ == "__main__":
    main()

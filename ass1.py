    import pymysql
    import serial
    from datetime import datetime
    import time

    # --- Configuration ---
    DB_HOST = "localhost"
    DB_USER = "kali"
    DB_PASSWORD = ""
    DB_NAME = "assignment1"

    SERIAL_PORT = '/dev/ttyS0'  # or '/dev/ttyACM0'
    BAUD_RATE = 9600


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
            # Soft reset
            ser.setDTR(False)
            time.sleep(1)
            ser.flushInput()
            ser.setDTR(True)
            time.sleep(2)  # wait for Arduino to initialize

            print("📡 Listening for RFID scans...")
            while True:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("LOG:"):
                    try:
                        parts = line.split(",")
                        uid = parts[0][4:].strip()  # remove "LOG:"
                        status = parts[1].strip()
                        # timestamp is generated from Raspberry Pi time
                        log_to_db(uid, status)
                    except Exception as e:
                        print(f"⚠️ Failed to parse line: {line} → {e}")

        except serial.SerialException as e:
            print(f"❌ Serial port error: {e}")

        except KeyboardInterrupt:
            print("\n🛑 Program terminated by user.")


    if __name__ == "__main__":
        main()

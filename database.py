import serial
import pymysql

device = '/dev/ttyS0'

adruino = serial.Serial(device,9600)
data = adruino.readline()
print(data)
dbConn = pymysql.connect("localhost","kali","","temperature_db") or die("cold not");

print (dbConn)
with dbConn:
    cursor = dbConn.cursor
    cursor.execute("INSERT INTO templog (temperature) VALUES(%s)"%(data))
    dbConn.commit
    cursor.close()

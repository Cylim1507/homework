import serial
import time
from flask import Flask, render_template

app = Flask(__name__)

# Dictionary of pins with name of pin and state ON/OFF
pins = {
    2 : {'name' : 'PIN 2', 'state' : 0 },
    3 : {'name' : 'PIN 3', 'state' : 0 }
    }
    
# Main function when accessing the website
@app.route("/")
def index():
    # TODO: Read the status of the pins ON/OFF and update dictionary
    
    #This data wii be sent to index.html (pins dictionary)
    templateData = { 'pins' : pins }
    
    # Pass the template data into the template index.html and return it
    return render_template('index.html', **templateData)

# Function with buttons that toggle depending on the status
@app.route("/<changePin>/<toggle>")
def toggle_function(changePin, toggle):
    # Convert the pin from the URL into an interger:
    changePin = int(changePin)
    # Get the device name for the pin being chnaged:
    deviceName = pins[changePin]['name']
    # If the action part of the URL is "on," execute the code intended below:
    if toggle == "on":
        #Set the pin high
        if changePin == 2:
            ser.write(b"1")
            pins[changePin]['state'] = 1
        if changePin == 3:
            ser.write(b"3")
            pins[changePin]['state'] = 1
        #Save the status message to be passed into the template:
        message = "Turned" + deviceName + "on."
    if toggle == "off":
        if changePin == 2:
            ser.write(b"2")
            pins[changePin]['state'] = 0
        if changePin == 3:
            ser.write(b"4")
            pins[changePin]['state'] = 0
        #Set the pin low
        message = "Turned" + deviceName + "off."
    
    #This data wii be sent to index.html (pins dictionary)
    templateData = { 'pins' : pins }
    
    # Pass the template data into the template index.html and return it
    return render_template('index.html', **templateData)

#Function to send simple commands
@app.route("/<action>")
def action(action):
    if action == 'action1':
        ser.write(b"1")
        pins[2]['state'] = 1
    if action == 'action2':
        ser.write(b"2")
        pins[2]['state'] = 0
    if action == 'action3':
        ser.write(b"3")
        pins[3]['state'] = 1
    if action == 'action4':
        ser.write(b"4")
        pins[3]['state'] = 0
    
    #This data wii be sent to index.html (pins dictionary)
    templateData = { 'pins' : pins }
    
    # Pass the template data into the template index.html and return it
    return render_template('index.html', **templateData)

# Main function, set up serial bus, indicate port for the webserver,
# ans start the service.
if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyS0', 9600, timeout = 1)
    ser.flush()
    app.run(host='0.0.0.0', port = 80, debug = True)
    
    

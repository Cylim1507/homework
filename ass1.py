from gpiozero import Buzzer, MCP3008
from time import sleep

# Setup
buzzer = Buzzer(17)  # GPIO17 (pin 11)
fsr = MCP3008(channel=0)  # FSR via ADC on channel 0

while True:
    print(f"Force sensor reading: {fsr.value}")
    if fsr.value < 0.1:  # Adjust threshold
        buzzer.on()
        sleep(0.5)
        buzzer.off()
    sleep(0.5)

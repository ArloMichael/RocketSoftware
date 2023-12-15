import RPi.GPIO as GPIO
import serial
import time
import pynmea2
from pprint import pprint

ser = serial.Serial('/dev/ttyS0', 9600)
ser.flushInput()

powerKey = 4
rec_buff = ''
time_count = 0
data = {}
altitudes = []
times = []

def calculate_current_speed(altitudes, times):
    """
    Calculate the current speed from a list of altitudes and corresponding times.

    Parameters:
    altitudes (list): A list of altitude measurements.
    times (list): A list of time measurements corresponding to the altitudes.

    Returns:
    float: The current speed calculated from the most recent altitude measurements.
    """
    if len(altitudes) < 2 or len(times) < 2:
        return 0

    # Calculate the difference in altitude and time for the last two points
    delta_altitude = altitudes[-1] - altitudes[-2]
    delta_time = times[-1] - times[-2]

    # Calculate the current speed
    current_speed = delta_altitude / delta_time

    return abs(current_speed) * 3.6

def parse_cgnsinf(data: str):
    # Strip any command prefixes and split the data by commas
    clean_data = data.replace("+CGNSINF: ", "").strip("\r\nOK\r\n")
    components = clean_data.split(",")

    # Padding the list to make sure it has the required number of elements
    while len(components) < 19:
        components.append(None)

    try:
        speed = calculate_current_speed(altitudes, times)
    except Exception as e:
        print(e)

    # Parse components into a dictionary
    parsed_data = {
        #"GNSS Run Status": components[0].replace("AT+CGNSINF\r\r\n",""),
        #"Status": int(components[1]) > 0,
        "UTC Date & Time": components[2],
        "Latitude": components[3],
        "Longitude": components[4],
        "Altitude": components[5],
        #"Speed Over Ground": components[6],
        #"Course Over Ground": components[7],
        #"Fix Mode": components[8],
        #"Reserved1": components[9],
        "HDOP": components[10],
        "PDOP": components[11],
        "VDOP": components[12],
        #"Reserved2": components[13],
        "Satellites": components[14],
        "Speed": f"{round(speed, 3):.3f}"
        #"GNSS Satellites Used": components[15],
        #"GLONASS Satellites Used": components[16],
        #"Reserved3": components[17],
        #"C/N0 max": components[18]
    }

    if components[5]:
        altitudes.append(float(components[5]))
        times.append(int(components[2][:-4]))

    return parsed_data

def sendAt(command, back, timeout):
    global data
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if rec_buff != '':
        if back not in rec_buff.decode():
            return 0
        else:
            try:
                data = parse_cgnsinf(rec_buff.decode())
            except Exception as e:
                print(e)

            return 1
    else:
        print('GPS is not ready')
        return 0


def position(callback = None):
    rec_null = True
    answer = 0
    print('Starting GPS session...')
    rec_buff = ''
    time.sleep(5)
    sendAt('AT+CGNSPWR=1', 'OK', 0.1)
    while rec_null:
        answer = sendAt('AT+CGNSINF', '+CGNSINF: ', 1)
        if 1 == answer:
            answer = 0

            if callback:
                callback(data) # IMPORTANT: THIS IS WHERE THE GPS DATA IS OUTPUT

            if ',,,,,,' in rec_buff:
                print('GPS is not ready')
                rec_null = False
                time.sleep(1)
        else:
            print('error %d' % answer)
            rec_buff = ''
            sendAt('AT+CGNSPWR=0', 'OK', 1)
            return False
        time.sleep(1.5)


def powerOn(powerKey = 4):
    print('SIM7080X is starting...')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(powerKey, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(powerKey, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(powerKey, GPIO.LOW)
    time.sleep(5)


def powerDown(powerKey = 4):
    print('SIM7080X is loging off...')
    if ser != None:
        ser.close()
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(powerKey, GPIO.OUT)
    GPIO.output(powerKey, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(powerKey, GPIO.LOW)
    GPIO.cleanup()
    time.sleep(5)
    print('Goodbye!')


def init():
    while True:
        # simcom module uart may be fool,so it is better to send much times when it starts.
        ser.write('AT\r\n'.encode())
        time.sleep(1)
        ser.write('AT\r\n'.encode())
        time.sleep(1)
        ser.write('AT\r\n'.encode())
        time.sleep(1)
        if ser.inWaiting():
            time.sleep(0.01)
            recBuff = ser.read(ser.inWaiting())
            print('SIM7080X is ready!\r\n')
            #print('try to start\r\n' + recBuff.decode())
            if 'OK' in recBuff.decode():
                recBuff = ''
                break
        else:
            powerOn(powerKey)
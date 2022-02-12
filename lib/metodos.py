def map(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)
    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def constrain(value, min, max):
    if value <= min:
        value = min
    elif value >= max:
        value = max
    return value

import machine
from machine import Pin
# Led Azul para verificar fisicamente el envio de los datos
led = machine.Pin(2, machine.Pin.OUT)
led.off()
def sendQuery(conn, query):
    try:
        led.on()
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        led.off()
    except Exception as inst:
        led.off()
        print(type(inst))
        print("Reinicio ERROR...")
        machine.reset()
        
def findDevice(conn, mac):
    cur = conn.cursor()
    cur.execute("SELECT d.id_dispositivo FROM dispositivo as d WHERE d.mac='"+mac+"'")
    result = cur.fetchone()
    # Retornar si existe
    if result is not None:
        return result[0]
    # Si no Registrar
    else:
        cur.execute("INSERT INTO dispositivo(nombre, mac, activo) VALUES('Prototipo2', '"+mac+"', true)")
        conn.commit()
        cur.execute("SELECT d.id_dispositivo FROM dispositivo as d WHERE d.mac='"+mac+"'")
        result = cur.fetchone()
        if result is not None:
            return result[0]
    return None

import lib.ads1x15 as ads1x15
def adsInstance(i2c):
    adsAdd = 0x48
    if adsAdd in i2c.scan():
        print("ADS Encontrado")
        return ads1x15.ADS1115(i2c, address=0x48, gain=2)
    print("Sin ADS")
    return None
    

def adsReadPin(ads, pin):
    # Samples per second
    # 4 _DR_1600SPS,  1600/128
    # 5 _DR_2400SPS,  2400/250
    try:
        if ads is not None:
            return ads.read(rate=5, channel1=pin)
    except:
        print("Fallo al leer Modulo ADS")
    return None

def adsReadPinMap(ads, data, pin):
    value = adsReadPin(ads, pin)
    if pin == 0:
        value = map(value, data['Vx1'], data['Vx2'], data['Gx1'], data['Gx2'])
    elif pin == 1:
        value = map(value, data['Vy1'], data['Vy2'], data['Gy1'], data['Gy2'])
    elif pin == 2:
        value = map(value, data['Vz1'], data['Vz2'], data['Gz1'], data['Gz2'])
    return value

def co2Map(data, value):
    value = map(value, data['Vc1'], data['Vc2'], data['Pc1'], data['Pc2'])
    value = constrain(value, 0, 3000)
    return value



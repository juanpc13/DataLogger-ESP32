import machine, ubinascii, time, dht
from machine import Pin, SoftI2C, ADC, Timer
import lib.micropg as micropg
from lib.metodos import *

# MAC del dispositivo
mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
# Conexion con la BD
conn = micropg.connect(host=data['hostname'], port=data['db_port'], user=data['db_user'], password=data['db_password'], database=data['db_name'], use_ssl=False)
# Id del dispositivo
id_dispositivo = findDevice(conn, mac)
# i2c con modulo de ADS
i2c = None
#i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000)
ads = None
#ads = adsInstance(i2c)
# relay que accion la GasCard y el MOTOR
relay = Pin(13, Pin.OUT)
relay.off()
# Declaracion para leer co2 (0.4v - 0 ppm) a (2.0v - 3000 ppm)
# Fijar 1dB attenuation (voltage rango 0.0v - 3.6v)
co2 = ADC(Pin(33))
co2.atten(ADC.ATTN_11DB)
# Modulo de DHT Temp y Humedad
dht = dht.DHT22(machine.Pin(4))
#Variables del timmer y extras
logQuery = ""
loopCounter = 0
timerLoop = Timer(0)

def showRawData(times=10):
    for i in range(times):
        print(logQuery)
        time.sleep(1)

def getAcelerometroQuery():
    global id_dispositivo
    # Si el acelerometro esta declarado enviar datos
    if ads is not None:
        # Plantilla de Query para Acelerometro
        query = "INSERT INTO acelerometro(id_dispositivo,x,y,z) VALUES(?,?,?,?);"
        query = query.replace('?',str(id_dispositivo), 1)
        # Iterador de los 3 EJES(X, Y y Z)
        for i in range(3):
            # Obtener Datos de i corresponde al pin A0 a A2 del ADS en posicion 0 al 2
            #eje = adsReadPin(ads, i)
            eje = adsReadPinMap(ads, data, i)
            if eje is not None:
                #eje = map(eje, calibration["xVOL1"], calibration["xVOL2"], calibration["xACE1"], calibration["xACE2"])
                query = query.replace('?', '{:.8f}'.format(eje), 1)
                
        # Se retorna la Query creada si no hay vacios con "?"
        if "?" not in query:
            return query
    return None

def getCo2Query():
    global id_dispositivo, loopCounter
    # Si el contador esta entre 0 minutos y 12 minutos encender gascard y generar query
    if loopCounter >= 60*0 and loopCounter <= 60*12:
        relay.on()
        # Si se encuentra entre el minuto 2 y el minuto 12 enviar datos
        if loopCounter >= 60*2 and loopCounter <= 60*12:
            # Plantilla de Query para Acelerometro
            query = "INSERT INTO co2(id_dispositivo, ppm) VALUES(?,?);"
            query = query.replace('?',str(id_dispositivo), 1)            
            ppm = (co2.read() + co2.read())/2
            ppm = co2Map(data, ppm)
            query = query.replace('?',str(ppm), 1)                    
            # Se envia la Query creada si no hay vacios con "?"
            if "?" not in query:
                return query
    # Si el contador excede los 60 minutos reiniciar
    elif loopCounter >= 60*60:
        loopCounter = 0
    # Ultima condicion si no cumple ninguna de las anteriores apagar la gascard
    else:
        relay.off()
    return None
def getHumedadQuery(measure):
    global dht, id_dispositivo
    # Plantilla de Query para Acelerometro
    query = "INSERT INTO humedad(id_dispositivo, rh) VALUES(?,?);"
    query = query.replace('?',str(id_dispositivo), 1)
    if measure:
        try:
            dht.measure()
        except:
            return None
    query = query.replace('?',str(dht.humidity()), 1)
    # Se envia la Query creada si no hay vacios con "?"
    if "?" not in query:
        return query
    return None
def getTemperaturaQuery(measure):
    global dht, id_dispositivo
    # Plantilla de Query para Acelerometro
    query = "INSERT INTO temperatura(id_dispositivo, temp) VALUES(?,?);"
    query = query.replace('?',str(id_dispositivo), 1)
    if measure:
        try:
            dht.measure()
        except:
            return None
    query = query.replace('?',str(dht.temperature()), 1)
    # Se envia la Query creada si no hay vacios con "?"
    if "?" not in query:
        return query
    return None
def app():
    global dht, loopCounter, conn, logQuery
    # Encabezado para tiempo de el salvador
    finalQuery = "SET TIMEZONE='America/El_Salvador';"
    firstSize = len(finalQuery)
    # Condicion de Mod de 1 segundo con sus QUERYS
    if loopCounter % 1 == 0:
        # Acelerometro
        query = getAcelerometroQuery()
        if query is not None:
            finalQuery += query
    # Condicion de Mod de 2 segundos con sus QUERYS
    if loopCounter % 2 == 0:
        # Co2
        query = getCo2Query()
        if query is not None:
            finalQuery += query
        # Humedad y Temp
        dht.measure()#Se mide AQUI
        query = getHumedadQuery(False)
        if query is not None:
            finalQuery += query
        query = getTemperaturaQuery(False)
        if query is not None:
            finalQuery += query
    # Se envia todo lo acumulado si ha cambiado
    lastSize = len(finalQuery)
    if lastSize > firstSize:
        sendQuery(conn, finalQuery)
        logQuery = finalQuery
    # Aumentar el contador
    loopCounter += 1
def play():
    # timmer de cada segundo para verificar funcion principal
    timerLoop.init(period=1000, mode=Timer.PERIODIC, callback=lambda t:app())
def stop():
    relay.off()
    timerLoop.deinit()
play()
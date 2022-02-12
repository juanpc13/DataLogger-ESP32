# This file is executed on every boot (including wake-boot from deepsleep)
import esp
#esp.osdebug(None)
import time

#Cargar configuraciones
import ujson
f = open("data.json")
data = ujson.loads(f.read())
f.close()

# Se conecta si esta disponible
import network
# Se crea punto de acceso propio para configurarse
print('Se crea Punto de Acceso Wifi')
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(authmode=3, essid=data['ap_ssid'], password=data['ap_password'])
ap.config(max_clients=10)
while ap.active() == False:
    pass
# create station interface
wlan = network.WLAN(network.STA_IF)
# activate the interface
wlan.active(True)
# lista de nombres wifi encontrados
wifi_names = [x[0] for x in wlan.scan()]
# Si existe en la lista conectarse a la red
print('Conectandose al Wifi configurado...')
if data['sta_ssid'].encode('ascii') in wifi_names:
    wlan.connect(data['sta_ssid'], data['sta_password']) # connect to an AP
    #15 segundos para conectar al wifi
    for i in range(15):
        if not wlan.isconnected():
            print('Conectando a',data['sta_ssid'],' Intento ',str(i+1))
            time.sleep(1)
#Mostrar las configuraciones
#print(wlan.config('mac'))
def showInfo():
    print(wlan.ifconfig())
showInfo()

#Se importa la interfaz WEB
import webrepl
webrepl.start(password=data['ap_password'])

import gc
gc.collect()
gc.mem_free()
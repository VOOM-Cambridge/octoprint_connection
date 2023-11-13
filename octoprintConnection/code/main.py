# script to collect octoprint data and update datebase with key data via mqtt messeages
import tomli
from octorest import OctoRest
import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# find the config file 
with open('config/printer_config.toml', 'rb') as machine_file:
    config_printer = tomli.load(machine_file)

num_print = len(config_printer["printer"])
frequency = config_printer["constant"]["update_frequency"]

def make_client(urlPrinter, apiKeyPrinter):
    try:
        client = OctoRest(url=urlPrinter, apikey=apiKeyPrinter)
        return client
    except Exception as e:
        print(e)

def on_pub(client, userdata, result):
    print("Published MQTT")
    pass

def send_data_mqtt(client, data, broker, port):
    for dat in data:
        mess = json.dumps(dat)
        client.on_publish = on_pub
        client.connect(broker, port)
        client.publish("printerData/" + dat["name"] + "/", mess)

# MQTT data format when printing
# {"name", "printer_1", "status": 1, "job_file": "name of file", "time_left": "100" (seconds), "progress": "0.55", "material_use": 100 (m), }
# MQTT data format when not printing
# {"name", "printer_1", "status": 0, "job_file": "", "time_left": "0" (seconds), "progress": "100", "material_use": 100 (m),}

timeNow = datetime.now()
time_lastMqtt = datetime(timeNow.year, timeNow.month, timeNow.day, timeNow.hour - 1, timeNow.minute, timeNow.second)
# find the data from octoprint 
while True:
    if (datetime.now() - time_lastMqtt).total_seconds() >= frequency:
        print("finding data")
        data = []
        time_lastMqtt = datetime.now()
        for printer in config_printer["printer"]:
            try:
                client = make_client(printer["ipAdress"], printer["APIkey"])
                client.state()
                connection =True
            except:
                print("Can't connect to: " + printer["name"])
                connection = False

            payload = {}
            if connection == True:
                # find data needed 
                payload["name"] = printer["name"]
                payload["timestamp"] = str(datetime.now())
                if client.state() == "Printing":
                    payload["status"] = 1
                    payload["material_use"] = client.job_info()['job']['filament']['tool0']['length']
                    payload["progress"] = client.job_info()['progress']['completion']
                    payload["time_left"] = client.job_info()['progress']['printTimeLeft']
                else:
                    payload["status"] = 0
                    payload["material_use"] = 0
                    payload["progress"] = 0
                    payload["time_left"] = 0
                
            print(payload)
            if payload != {}:
                data.append(payload)

        clientmqtt = mqtt.Client("printerAPI")
        send_data_mqtt(clientmqtt, data, config_printer["mqtt"]["broker"], config_printer["mqtt"]["port"])
        print("data sent")
    else:
        time.sleep(0.5)

    
# send data via mqtt and to sql local database possibly 


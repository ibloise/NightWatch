import json
import pandas as pd
from datetime import datetime
from watchersTools import *

#Functions
def generateSeqDates(start, end, dateformat = "%Y-%m-%d"):
    try:
        start = datetime.strptime(start, dateformat)
        end = datetime.strptime(end, dateformat)
        time_list = pd.date_range(start=start, end=end).strftime(dateformat).to_list()
        return time_list
    except:
        print("No ha sido posible generar la secuencia. ¿Has usado el formato de fecha correcto?")

#Functions

def importWatcherList(listDicts): #Hay que reconvertir esto en clase
    watcher_list = [Watcher(value["id"], value["name"], value["active"], value["restriction"]) for value in listDicts]
    return watcher_list

def importJSON(jsonFile):
    try:
        with open(jsonFile, mode= "r") as f:
            readDict = json.load(f)
        return readDict
    except:
        print("No se ha podido abrir el archivo")

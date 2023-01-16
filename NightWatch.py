from watchCalendar import *
from tools import *
from watchersTools import *



#Importamos los watchers
watcherList = importWatcherList(importJSON("watchers.json"))



def blockDays(watcherList, idBlockList, blockDaysList):
    for idx, watcher in enumerate(watcherList):
        if watcher.id in idBlockList:
            tempWatcher = watcher
            tempWatcher.set_block_days(blockDaysList)
            watcherList[idx] = tempWatcher
    return watcherList



for idx, watcher in enumerate(watcherList):
    if watcher.id == '1005':
        tempWatcher = watcher
        tempWatcher.setSpecialWatch(2,4,8)
        tempWatcher.setSpecialWatch(3,4,8)
        watcherList[idx] = tempWatcher

blockDays(watcherList,['6222'], generateSeqDates('2023-03-09','2023-03-12'))
blockDays(watcherList,['1005'], generateSeqDates('2023-02-03', '2023-02-07'))


#Creacion del calendario
watcherCalendar = WatchCalendar([2,3], 2023)


#Incorporamos los guardianes a watcherCalendar

watcherCalendar.import_watchers(watcherList)


#Incorporamos las estadísticas

watcherCalendar.importStats("stats_enero_2.csv")



offDays = ["2023-03-20"]
watcherCalendar.set_offdays(offDays)
watcherCalendar.changeOffDays()
watcherCalendar.set_bridge("San Jose", generateSeqDates('2023-03-17', '2023-03-20'))


#watcherCalendar.assignID("6222", "2023-01-01")
#watcherCalendar.assignID("1005", "2023-01-06")

watcherCalendar.assignBridges()
watcherCalendar.assignWeekend()
watcherCalendar.assignWorkingDays()

watcherCalendar.dateDf.to_csv("guardiasFebreroMarzo_sinPaloma.csv")
watcherCalendar.stats.to_csv("statsFebreroMarzo_sinPaloma.csv")


exit()
#Configuración de festivos

offdayList = ["2022-10-12", "2022-11-09", "2022-11-01"]

watcherCalendar.set_offdays(offdayList)


##Creamos los puentes

novemberBridge = {"Todos los Santos" : generateSeqDates("2022-10-29", "2022-11-01")}

watcherCalendar.set_bridge("Santos", novemberBridge["Todos los Santos"])

decemberBridge = {
    "Constitucion primera parte" : generateSeqDates("2022-12-02", "2022-12-05"),
"Constitucion segunda parte" : generateSeqDates("2022-12-06", "2022-12-08"),
"Constitucion tercera parte" : generateSeqDates("2022-12-09", "2022-12-11")
}

#watcherCalendar.set_bridge("Constitucion1", decemberBridge["Constitucion primera parte"])
#watcherCalendar.set_bridge("Constitucion2", decemberBridge["Constitucion segunda parte"])
#watcherCalendar.set_bridge("Constitucion3", decemberBridge["Constitucion tercera parte"])


#Renombramos los festivos 

watcherCalendar.changeOffDays()

#watcherCalendar.assignID("DIA_BLOQUEADO", "2022-12-24")
#watcherCalendar.assignID("DIA_BLOQUEADO", "2022-12-25")
#watcherCalendar.assignID("DIA_BLOQUEADO", "2022-12-31")
#Comenzamos el reparto

watcherCalendar.assignBridges()
watcherCalendar.assignWeekend()
watcherCalendar.assignWorkingDays()
print(watcherCalendar.dateDf.to_string())
watcherCalendar.dateDf.to_csv("guardias_octubreNoviembre.csv")
watcherCalendar.stats.to_csv("stats_summary_modified.csv")

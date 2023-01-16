
import sys
import numpy as np
import calendar as cal
import pandas as pd
from datetime import datetime, timedelta
from itertools import cycle
from watchersTools import *


#ToDo: Hay que seguir modularizando el codigo para reducir la variabilidad y tener más control
#   El control de asignación de jueves no está funcionando. Asigna jueves con domingo y sábado
#   Hay que controlar la asignación global de guardias:
#   Penalizar dobletes
#   Equilibrar guardias globales para que aquellos que tengan 4 laborables reciban 0-1 festivo, pero no 2.

## Hay que eliminar todo el hardcodeo que hay, que empieza a ser preocupante

##Conf
weekdays = {
    0 : {
    "en_name" :  "Monday",
    "sp_name" : "Lunes",
    "labour" :  True 
    } , 
    1 : {
        "en_name" : "Tuesday",
        "sp_name" : "Martes",
        "labour" : True
    } ,
    2 : {
        "en_name" : "Wednesday",
        "sp_name" : "Miércoles",
        "labour" : True
    } , 
    3 : {
        "en_name" : "Thursday",
        "sp_name" :  "Jueves",
        "labour" : True
    } , 
    4 : {
        "en_name" : "Friday",
        "sp_name" : "Viernes",
        "labour" : True
    } , 
    5 : {
        "en_name" : "Saturday", 
        "sp_name" : "Sábado" , 
        "labour" : False
    }, 
    6 : {
        "en_name" : "Sunday" , 
        "sp_name" : "Domingo" , 
        "labour" : False
    }
    
}


#Classes
class WatchCalendar():
    """
    WatchCalendar
    """
    def __init__(self, months, year, fill_weeks = True):
        self.months = months
        self.year = year
        self.fill_weeks = fill_weeks
        self.calendar = cal.TextCalendar(self.year)
        self.calendar.setfirstweekday(cal.MONDAY)
        self.datetime_format = "%Y-%m-%d" #A archivo de constantes!
        self.bridges = {}
        self.calcs = {}
        self.changeOffDaysLog = {}
        self.workerStats = {}
        self.minLabours = 3
        self.maxLabours = 7
        #Creación del diccionario de fechas
        self.date_dict = {}
        for month in self.months:
            for date in self.calendar.itermonthdates(self.year, month):
                if self.fill_weeks and int(date.strftime("%m")) != month:
                    continue
                weekday_data = weekdays[date.weekday()]
                day_name, labour = (weekday_data["sp_name"], weekday_data["labour"])
                self.date_dict[date.strftime(self.datetime_format)] = {
                    "day_name" : day_name, 
                    "labour" :  labour,
                }
        self.buildDataframe()
    
    def calcDaysDist(self): #Muy hardcodeada. Realmente habría que depreciar esta parte y empezar a hacer los calculos dinámicamente
        """
        Calcula la distribución de días de los meses.
        """
        self.calcs = {month : {} for month in self.months}
        for month in self.months:
            labDays = len(self.dateDf[(self.dateDf["month"] == month) & (self.dateDf["labour"] == True ) & (self.dateDf["bridge"] == "non-bridge")].index)
            offDays = len(self.dateDf[(self.dateDf["month"] == month) & (self.dateDf["labour"] == False ) & (self.dateDf["bridge"] == "non-bridge")].index)
            bridgeOffDays = len(self.dateDf[(self.dateDf["month"] == month) & (self.dateDf["labour"] == False ) & (self.dateDf["bridge"] == "bridge")].index)
            bridgeLabDays = len(self.dateDf[(self.dateDf["month"] == month) & (self.dateDf["labour"] == True ) & (self.dateDf["bridge"] == "bridge")].index)

            self.calcs[month] = {"labours" : labDays, "off_days" : offDays, "bridgeOffDays" : bridgeOffDays, "bridgeLabDays" : bridgeLabDays}

    def checkSpecials(self):
        """
        Almacena la información sobre trabajadores que tengan características especiales
        """
        self.specialDict = {str(month) : {"special" : [], "non-special" : []} for month in self.months} 
        for id, watcher in self.watcherDict.items():
            if watcher.specialWatch:
                exceptMonths = {month for month in list(watcher.specialWatch.keys()) if month in self.specialDict.keys()}
                nonExceptMonths = {month for month in self.specialDict.keys() if month not in exceptMonths}
                for month in exceptMonths:
                    self.specialDict[month]["special"].append(id)
                for month in nonExceptMonths:
                    self.specialDict[month]["non-special"].append(id)
            else:
                for month in self.specialDict.keys():
                    self.specialDict[str(month)]["non-special"].append(id)

    
    def distributeDays(self, iterMonths):
        """
        Distribuye los días entre trabajadores con condiciones especiales, asignados y retirados.
        Esta función es esencial para controlar el número mínimo de guardias que se pueden hacer.
        Es necesario optimizar su funcionamiento!
        """
        #El problema central está aquí:
        #Este código se ejecuta de forma independiente para cada mes
        # Por tanto, asigna los días SIN CONSIDERAR los meses futuros
        #En principio no debería dar problemas, pero al tener un megapuente como el de diciemnbre todo se va al carajo
         
        #Requiere de stats, specials y calcs.
        ##Debe checkear si alguien tiene puesto ya algún laboral
        self.calcDaysDist()
        self.checkSpecials()
        print("Distribuyendo días")
        self.watcherDistribution = {month : {} for month in iterMonths}
        ratioStats = self.stats.copy()
        for month in iterMonths:
            print(f"Asignando {month}")
            #Informamos de los meses erróneo y continuamos el bucle
            if month not in self.months:
                print(f"El mes {month} no está en la distribución")
                continue
            rest = 0
            removers = []
            specials = self.specialDict[str(month)]["special"]
            iterSpecials = [id for id in specials if specials]
            if iterSpecials:
                for id in iterSpecials:
                    print(f"Calculando guardias reservadas para {id}")
                    rest += self.watcherDict[id].specialWatch[str(month)]["min"]
            print(f"Un total de {str(rest)} guardias están reservadas")

            #Buscamos quien tiene ya laborables asignados:

            workersRequired = list(self.dateDf[(self.dateDf["bridge"] == "bridge") & (self.dateDf["labour"] == True) & (self.dateDf["month"] == month)]["id"])
            if workersRequired:
                print(f"Es obligatorio incluir a los siguientes trabajadores en {month}:")
                print(*workersRequired, sep = ", ")
            else:
                print("No hay trabajadores obligatorios")

            #A continuación calculamos el remanente:
            #Hay que ir eliminando calcs de todo el codigo. Estos cálculso deberían realizarse solos
            query = f"month == {month} & labour == True & bridge == 'non-bridge' & id.isnull()"
            correctedLabours = self.dateDf.query(query).shape[0] - rest
            print(f"Disponibles {str(correctedLabours)} guardias")
            workers = self.specialDict[str(month)]["non-special"]
            ratio = correctedLabours / len(workers)
            print(f"Ratio : {str(ratio)}")
            exceptionWheel = self.setWheel(ratioStats, criterialList=["labours"], wheelType="exceptionsRatio")
            print("Calculando candidatos")
            print(exceptionWheel)
            exceptionsCandidates = list(exceptionWheel.id)
            #Búsqueda de candidatos
            while ratio < self.minLabours and len(workers) > 0:
                print("Corrigiendo ratio" )
                exceptionCandidate = exceptionsCandidates[-1]
                if exceptionCandidate not in workersRequired:
                    print(f"Se va a proceder a eliminar a {exceptionCandidate}")
                    exceptionsCandidates.remove(exceptionCandidate)
                    try:
                        workers.remove(exceptionCandidate)
                        removers.append(exceptionCandidate)
                    except:
                        print(f"{exceptionCandidate} no está en lista de trabajo")
                    ratio = correctedLabours/len(workers)
                    print(f"Ratio corregido: {str(ratio)}")
                else:
                    print(f"{exceptionCandidate} debe cubrir guardias laborales en {month}")
                    exceptionsCandidates.remove(exceptionCandidate)
            #Ahora guardamos la información:
            for id in workers:
                print(f"Actualizando stats temporales: {id} incrementa sus laborales en {str(int(ratio))}")
                ratioStats = self.updateStats(id, col = "labours", stats = ratioStats, increase = int(ratio), inplace=False)
            self.watcherDistribution[month] = {"special" : iterSpecials, "non-special" : workers, "deleted" : removers}

    def fixerDistDays():
        #Este metodo debe revisar la distribución de días y corregirla 
        #Para ello debe coger la watcherDistribution y comprobar si hay uno o varios que estén en TODAS las deleted
        #En ese caso debe calcular si, en el período estudiado, hay guardias suficientes para todos:
        #Por ejemplo: 3 meses = 3*20 = 60
        #SI 60/nfacultativos > minimo (hay que pensar como corregir al de guardias)
        #el programa debe comprobar si los que están completamente excluidos puedne entrar todos o solo algunso
        #a los que puedan entrar, debe eliminar a alguno de los que están (preferiblemente el que mas este y de un mes en el que no tenga laboralesk)
        pass

    def set_bridge(self, bridge_name, dates_ls): #Pendiente: control de errores, testar que los días existen en el calendario. No debe cambiarlos a offday
        self.bridges[bridge_name] = dates_ls
        #dateFormat = pd.to_datetime(dates_ls)
        #print(dateFormat)
        for date in dates_ls:
            self.dateDf.loc[date, "bridge"] = "bridge"

    def set_offdays(self,dates_ls): #Cambiamos el estado de fechas
        ##Comprobar que son todo fechas! ##Reconvertir todo esto a dataframe!!!!
        for date in dates_ls:
            if date in self.date_dict.keys():
                self.date_dict[date]["labour"] = False
                self.dateDf.loc[date, "labour"] = False
        self.calcDaysDist()
    
    def assignID(self, watcherID, date):
        #Comprobamos que el día está vacío?
        self.dateDf.at[date, "id"] = watcherID

    def buildDataframe(self):
        self.dateDf = pd.DataFrame.from_dict(self.date_dict, orient = "index")
        self.dateDf["id"] = np.nan
        self.dateDf["bridge"] = "non-bridge"
        self.dateDf.index = pd.to_datetime(self.dateDf.index)
        self.dateDf["month"]  = self.dateDf.index.month

    def set_labourday(self, dates_ls):
        for date in dates_ls:
            if date in self.date_dict.keys():
                self.date_dict[date]["labour"] = True
        self.calcDaysDist()

    def set_offdays_by_days(self, month, days):
        pass

    def import_watchers(self, watchers_list):
        """
        Recibe la lista de guardianes para poder realizar los cálculos
        """
        self.watcher_list = []
        for watcher in watchers_list:
            if isinstance(watcher, Watcher) and watcher.active:
                self.watcher_list.append(watcher)
            else:
                print(f"El objeto {watcher.id} no pertenece a la clase adecuada o está inactivo")
        self.buildWatcherDict()
    
    def buildWatcherDict(self):
        self.watcherDict = {watcher.id : watcher for watcher in self.watcher_list}

    def updateStats(self, id, col, stats = "", increase = 1, inplace=True):
        if inplace:
            self.stats.loc[self.stats.id == id, col] += increase
        else:
            stats.loc[stats.id == id, col] += increase
            return(stats)

    def CheckDifferences(self, list1, list2):
        mismatchs = list(set(list1).difference(list2))
        return mismatchs
    
    def importStats(self, stats): ##Hay que pasar las stats a una clase propia?
        #Transformamos las stats en dataframe.   
        ##colsStats debe ir al archivo de constantes
        colsStats = ['id', 'bridges_days', 'bridges_off_days', 'bridges_laboral_days', 'Lunes', 'Martes',  'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        self.stats = pd.DataFrame(columns = colsStats)
        #readStats = pd.read_json(json.dumps(stats), dtype={"id":str}) ##A deprecatear esta función:
        readStats = pd.read_csv(stats, dtype={"id":str})
        print(readStats)
        self.stats = pd.concat([self.stats, readStats]).fillna(0)
        ##Check for id

        inactives = self.CheckDifferences(self.stats["id"].to_list(), self.watcherDict.keys())
        if inactives:
            for id in inactives:
                print(f"{id} está inactivo. Se procede a eliminarlo de las ruedas")
                self.stats = self.stats[self.stats.id != id]

        mismatchs = self.CheckDifferences(self.watcherDict.keys(), self.stats["id"].to_list()) 
        print(mismatchs)
        if mismatchs: 
            for id in mismatchs:
                idRow = [id]
                idRow += [0 for i in range(len(self.stats.columns)-1)]
                self.stats.loc[len(self.stats)+1] = idRow


        #Esto debería ser una función y ejecutarse aquí y en cada updateStats
        self.stats["off_days"] = self.stats["Domingo"] + self.stats["Sábado"]
        self.stats["labours"] = self.stats["Lunes"] + self.stats["Martes"] + self.stats["Miércoles"] + self.stats["Jueves"] + self.stats["Viernes"]

        #self.number_of_workers = len(self.stats.index)
        #randoms = set()
        #print("Generating random numbers")
        #while len(randoms) < self.number_of_workers:
        #    value = np.random.randint(0, 1000)
        #    randoms.add(value)
        #self.stats["randoms"] = list(randoms)
        #print(self.stats)

    def assignBridges(self):
        """
        Función que asigna los puentes del calendario
        """
        #Realmente todos los métodos: el asignador de puentes, el corrector de fechas, y los asignadores de otros días
        #sería mejor tenerlos programados como métodos independientes a los que termina llamando create_watch_calendar

        if self.bridges:
            bridges_order_list = ["bridges_days", "bridges_laboral_days", "bridges_off_days"] #Sacar esto a archivo de configuracion
            
            for bridge, dates in self.bridges.items():
                choicer = 0
                candidates = set()
                #Rueda
                self.bridges_wheel = self.setWheel(self.stats, criterialList = bridges_order_list, wheelType = "bridge")
                print("Estadísticas calculadas: ")
                print(self.bridges_wheel)
                #Candidatos
                while len(candidates) < 2 and choicer < self.number_of_workers:
                    idWatcher = self.bridges_wheel["id"].iat[choicer]
                    print(f"Evaluando a {idWatcher}")
                    #exclusion = self.CheckDifferences(self.watcherDict[idWatcher].block_days, dates)
                    exclusion = [date for date in dates if date in self.watcherDict[idWatcher].block_days]
                    if not exclusion:
                        print(f"Candidato {idWatcher} asignado a puente {bridge}")
                        candidates.add(idWatcher)                        
                    else:
                        print(f"El candidato {idWatcher} tiene las siguientes exclusiones:")
                        print(exclusion)
                    choicer += 1
                if len(candidates) < 2:
                    print("No se han encontrado suficientes candidatos! Alguien debe liberar días")
                    sys.exit()
                #Asignacion
                iter_dates = zip(cycle(candidates), dates)
                for id, date in iter_dates:
                    print(f"Asignando el día {date} a {id}")
                    self.dateDf.at[date, "id"] = id
                    cols = ["bridges_days"]
                    if self.dateDf.at[date, "labour"]: 
                        cols += ["bridges_laboral_days"]
                    else:
                        cols += ["bridges_off_days"]
                    for col in cols:
                        self.updateStats(id, col = col)

    def assignWeekend(self): 
        #Obtenemos los días
        #Primero sábados y luego domingos -> Hay que meter la asignación de otros festivos!!
        ##Recorrer el dataframe, detectar si hay algún día festivo no sábado ni domingo ni puente y setearle el nombre a domingo! así se ejecuta en la iteración
        ##Guardar el index para devolverlo a su nombre al final!!!
        weekend = ["Sábado", "Domingo"]
        for weekDay in weekend:
            #Obtenemos la lista de días a asignar
            days = self.dateDf[(self.dateDf.day_name == weekDay) & (self.dateDf.bridge == "non-bridge")].index
            if weekDay == "Sábado":
                until = 2
            else:
                until = 1
            #Procedemos a la asignación. 
            for day in days:
                day = day.to_pydatetime().strftime(self.datetime_format)
            #Creamos la rueda cada vez que se completa la asignación de un día
                weekendWheelDf = self.setWheel(self.stats, criterialList = ["off_days", weekDay], wheelType = weekDay)
                weekendWheel = list(weekendWheelDf.id)
                self.assignDay(wheelList=weekendWheel, date= day, updateCols=[weekDay, "off_days"], checkUntilDay=until)
    
    def changeOffDays(self, dayName = "Domingo"):
        """
        Función que cambia los festivos semanales no de puente a un tipo determinado
        """
        laboralDays = ["Lunes", "Martes", "Miércoles", "Jueves"]
        for index, row in self.dateDf.iterrows():
            if row["day_name"] in laboralDays and row["labour"] == False and row["bridge"] == "non-bridge":
                self.dateDf.at[index, "day_name"] = dayName
                self.changeOffDaysLog[index] = dayName
                print(f"Se ha cambiar el día {index} a {dayName}")
    
    def assignDay(self, wheelList, date,  updateCols, updateWorkerStats =  False,checkNextDay = 1, checkUntilDay = 1):
        if pd.notnull(self.dateDf.at[date, "id"]) :
            print(f"{date} ya está ocupado y no va a asignarse")
            return None
        for worker in wheelList:
            print(f"Evaluando a {worker}")
            if self.globalCheck(date, worker, untilNextDay=checkNextDay, untilPreviousDay= checkUntilDay):
                print(f"{date} asignado a {worker}")
                self.dateDf.at[date, "id"] = worker
                if updateWorkerStats:
                    self.workerStats[worker] += -1
                    print("Actualizadas estadísticas")
                    print(self.workerStats)
                for col in updateCols:
                    self.updateStats(worker, col = col)
                break

    def assignWorkingDays(self):
        #Asignamos los días laborales. Requiere la existencia de self.watcherDistribution
        print("Iniciando asignación de laborables")
        self.distributeDays(iterMonths=self.months)
        for month in self.months: #Esto posiblemente pueda ir todo a unam isma funcion con weekend
            print(f"Distribuyendo días del mes {month}")
            print(self.watcherDistribution)
            ###Lista de workers para este mes:
            workers = self.watcherDistribution[month]["special"] + self.watcherDistribution[month]["non-special"]
            #self.watcherDict[id].specialWatch[month]["min"]
            self.workerStats = {worker: self.watcherDict[worker].specialWatch[str(month)]["min"] for worker in self.watcherDistribution[month]["special"]}
            self.workerStats.update({worker: self.minLabours for worker in self.watcherDistribution[month]["non-special"]})
            print("Estadísticas de asignación de laborables:")
            print(self.workerStats)

            ##Rueda de jueves y viernes
            weekDays = ["Jueves", "Viernes"] #A constantes

            for weekDay in weekDays: #Todo esto hay que convertirlo en una función!!!!!!!!!!!!!!
                days = self.dateDf[(self.dateDf.day_name == weekDay) & (self.dateDf.month == month) &(self.dateDf.bridge == "non-bridge") & self.dateDf.labour == True].index
                #La asignación de laborables habrá que sacarla de aquí

                #Define days
                if weekDay == "Jueves":
                    next = 3
                else:
                    next = 1

                for day in days:
                    day = day.to_pydatetime().strftime(self.datetime_format)
                    
                    wheelDf = self.setWheel(self.stats, criterialList=[weekDay, "labours", "bridges_laboral_days"], wheelType=weekDay)
                    workers = [worker for worker, value in self.workerStats.items() if value >0]
                    wheelList = [worker for worker in list(wheelDf.id) if worker in workers]

                    self.assignDay(wheelList, day, updateCols=[weekDay, "labours"], updateWorkerStats=True, checkNextDay=next)
            #Vamos a la rueda general:
            #Los laborables deben calcularse en función de los datos de la tabla
            query = f"month == {month} & labour == True & bridge == 'non-bridge' & id.isnull()"
            labours = self.dateDf.query(query).shape[0]

            print(f"Laborales restantes: {labours}")
            #Hay que asgnar el excedente:
            exc = labours - sum(self.workerStats.values())

            #Asignar excedentes:
            if exc > 0:
                print(f"Existe excedente de guardias: {exc}")
                wheelDf = self.setWheel(self.stats, criterialList=["labours", "bridges_laboral_days"], wheelType="excedentes")
                for n in range(exc):
                    candidate = [worker for worker in list(wheelDf.id) if worker in self.workerStats.keys()][n]
                    self.workerStats[candidate] += 1
                    print(f"Asignada una guardia extra a {candidate}")
            elif exc <0:
                print(f"No hay guardias suficientes en {month}!!! Se va a parar la asignación")
                sys.exit()

            #Para construir la rueda:
            #
            ##La iteración debe ocurrir para todos los laborales en excedente dle mes. Actualizar la lista de workers en cada giro
            print("Iniciando asignacion")
            print(self.workerStats)
            #Cambiar esto a query
            days = self.dateDf[(self.dateDf.id.isnull()) & (self.dateDf.month == month) &(self.dateDf.bridge == "non-bridge") & (self.dateDf.labour == True)].index
            if len(days) != labours:
                print("Los laborables no corresponden!!")
                sys.exit()

            ######El programa calcula mal las estadísticas!!! No tiene en cuenta los días de puente!!!
            for day in days: #Esto hay que convertirlo en función también
                day = day.to_pydatetime().strftime(self.datetime_format)
                workers = [worker for worker, value in self.workerStats.items() if value >0]
                wheelDf = self.setWheel(self.stats, criterialList=["labours", "bridges_laboral_days"], wheelType="labours")
                print("")
                print(f"Esquema de asignacion para {day}")
                print(self.workerStats)
                print(workers)

                wheelList = [worker for worker in list(wheelDf.id) if worker in workers]
                self.assignDay(wheelList= wheelList, date = day, updateCols= [self.dateDf.at[day, "day_name"], "labours"], updateWorkerStats= True)
        print("Estadística de reparto actualizadas:")
        print(self.workerStats)

    def checkCompatibility(self, date, idWatcher, untilPreviousDay=1, untilNextDay = 1):
        """
        Función que comprueba compatibilidad de salientes
        """
        print("Comprobando salientes")
        dateFormat = datetime.strptime(date, self.datetime_format)
        checkDays = list(range(-untilPreviousDay, 0)) + list(range(untilNextDay, 0, -1))
        for day in checkDays:
            try:
                if self.dateDf.loc[dateFormat + timedelta(day), "id"] == idWatcher:
                    print(f"{idWatcher} incompatible con día {date}")
                    return False

            except KeyError:
                print(f"No hay día previo o posterior para {idWatcher}")
                print("Por favor, comprueba las incompatibilidades")
                return True
        
        print(f"No se han encontrado incompatibilidades por saliente para {idWatcher}")
        return True
    
    def checkBlockDays(self, date, idWatcher):
        print("Comprobando días bloqueados")
        if date in self.watcherDict[idWatcher].block_days:
            print(f"{date} bloqueado")
            return False
        else:
            print(f"{date} está libre para {idWatcher}!")
            return True
        
    def checkFree(self, date): #Muchos problemas con las fechas. Hay que homogeneizarlo
        print("Comprobando que el día está libre")
        try:
            if not self.dateDf.at[date, "id"]:
                print(f"{date} está ocupado!")
                return False
            else:
                return True
        except:
            print("El formato fecha no se ha introducido correctamente!")
            sys.exit()

    def globalCheck(self, date, idWatcher, untilNextDay=1, untilPreviousDay=1):
        condition1 = self.checkCompatibility(date, idWatcher, untilNextDay, untilPreviousDay)
        condition2 = self.checkBlockDays(date, idWatcher)
        condition3 = self.checkFree(date)

        globalCond = condition1 and condition2 and condition3
        return globalCond

    def setWheel(self, df, criterialList, wheelType, random = True, verbose = True): 
        """
        Recibe un dataframe con stats y una lista de criterios y devuelve un dataframe con el orden de la rueda
        """
        if random:
            self.number_of_workers = len(self.stats.index)
            randoms = set()
            print("Generating random numbers")
            while len(randoms) < self.number_of_workers:
                value = np.random.randint(0, 1000)
                randoms.add(value)
            df["randoms"] = list(randoms)
            criterialList += ["randoms"]
        wheel = df.sort_values(by = criterialList, ascending = True).reset_index(drop=True).reset_index().rename(columns = {"index" : "order"})
        wheel["type"] = wheelType
        if verbose:
            print(f"Creada la rueda {wheelType}")
            print(wheel.to_string())

        return wheel

    def print_empty_calendar(self):
        pass

    def print_watch_calendar(self):
        pass
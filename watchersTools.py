

#Classes
class Watcher():
    def __init__(self, id, name, active = True, restriction = "no"):
        self.id = id
        self.name = name
        self.active = active
        self.restriction = restriction
        self.max_watch = {}
        self.min_watch = {}
        self.block_days = {}
        self.specialWatch = {}
    
    def set_inactive(self):
        self.active = False
    
    def set_active(self):
        self.active = True
    
    def set_restriction(self, restriction):
        if restriction in ["no", "weekend", "labour"]:
            self.restriction = restriction
        else:
            print("Only addmit one of the following values: no, weekend, labour")
            
    def set_max_watch(self, month, n):
        self.max_watch[month] = n
    def set_min_watch(self, month, n):
        self.min_watch[month] = n
    def setSpecialWatch(self, month, min, max):
        self.specialWatch.update({month : {"min" :  min, "max" : max}})
    def set_block_days(self, block_days):
        self.block_days = block_days


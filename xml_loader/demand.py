from datetime import time, datetime, date
class Demand():
    

    def __init__(self, demand_id):
        self.today = date.today()
        self.demand_id = demand_id
        self.start = []
        self.end = []
        self.minimum = []
        self.maks = [] 
        self.ideal = []
        self.time_delta = []
        self.time_step_length = None
    
    def add_info(self, start, end, maksimum, minimum, ideal):
        start = start.split(":")
        end = end.split(":")
        start = time(int(start[0]), int(start[1]))
        end = time(int(end[0]), int(end[1]))
        self.start.append(start)
        self.end.append(end)
        self.minimum.append(int(minimum))
        self.maks.append(int(maksimum))
        self.ideal.append(int(ideal))
        self.time_delta.append(datetime.combine(self.today, end) - datetime.combine(self.today,start))


    def __str__(self):
        return(self.demand_id)


from datetime import time, datetime, date


class Demand:
    def __init__(self, demand_id):
        self.today = date.today()
        self.demand_id = demand_id
        self.start = []
        self.end = []
        self.minimum = []
        self.maximum = []
        self.ideal = []
        self.time_delta = []
        self.time_step_length = None

    def add_info(self, start, end, maximum, minimum, ideal):
        start = start.split(":")
        end = end.split(":")
        if int(start[1]) != 0:
            start = float(start[0]) + (100 / (60 / float(start[1]))) / 100
        else:
            start = float(start[0]) + float(start[1])
        if int(end[1]) != 0:
            end = float(end[0]) + (100 / (60 / float(end[1]))) / 100
        else:
            end = float(end[0]) + float(end[1])
        self.start.append(start)
        self.end.append(end)
        self.minimum.append(int(minimum))
        self.maximum.append(int(maximum))
        self.ideal.append(int(ideal))
        # self.time_delta.append(datetime.combine(self.today, end) - datetime.combine(self.today,start))

    def add_info2(self, start, end, maximum, minimum, ideal):
        start = start.split(":")
        end = end.split(":")
        self.start.append(time(int(start[0]), int(start[1])))
        self.end.append(time(int(end[0]), int(end[1])))
        self.minimum.append(int(minimum))
        self.maximum.append(int(maximum))
        self.ideal.append(int(ideal))
        # self.time_delta.append(datetime.combine(self.today, end) - datetime.combine(self.today,start))

    def __str__(self):
        return self.demand_id

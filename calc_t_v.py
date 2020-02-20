import xml_loader.xml_loader as xl
from datetime import datetime




def get_time_periods():
    time_periods = []
    days = xl.get_demand()
    for day in days:
        for time in days[day].start:
            imp = ('{:.5}'.format(str(time)))
            if imp not in time_periods:
                time_periods.append(imp)
        
        for time in days[day].end:
            imp = ('{:.5}'.format(str(time)))
            if imp not in time_periods:
                time_periods.append(imp)


        for time in range(len(days[day].start)):
            tdelta = datetime.combine(day, days[day].end[time]) - datetime.combine(day,days[day].start[time]) 
            print(tdelta)
        
    print(time_periods)

get_time_periods()
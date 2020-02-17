import xml_loader.xml_loader as xl

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

print(time_periods)
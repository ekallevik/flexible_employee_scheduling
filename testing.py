import pytest

def test_covering_min_demand(y,demand_min, employees, competencies, time_periods):
    for c in competencies:
        for t in time_periods:
            assert sum(y[c,e,t] for e in employees) == demand_min[c,t]
            
                
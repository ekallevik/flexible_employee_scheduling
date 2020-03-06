import pytest
from model_class import *

@pytest.fixture
def variables_added():
    model = Optimization_model()
    model.add_variables()

@pytest.fixture
def constraints_added():
    model = Optimization_model()
    model.add_variables()
    model.add_constraints()

@pytest.fixture
def objective_added():
    model = Optimization_model()
    model.add_variables()
    model.add_constraints()
    model.set_objective()

@pytest.fixture
def model_optimized():
    model = Optimization_model()
    model.add_variables()
    model.add_constraints()
    model.set_objective()
    model.model.optimize()
    return model





def test_covering_min_demand(model_optimized):
    for c in model_optimized.competencies:
        for t in model_optimized.time_periods:
            assert sum(model_optimized.y[c,e,t].x for e in model_optimized.employees) == model_optimized.demand_min[c,t], "Demand not covered"
            
                
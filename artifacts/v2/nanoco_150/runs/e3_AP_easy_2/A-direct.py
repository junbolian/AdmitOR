import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    n = len(cost_matrix)
    m = len(cost_matrix[0])

    model = pyo.ConcreteModel()

    model.drivers = pyo.RangeSet(0, n - 1)
    model.rides = pyo.RangeSet(0, m - 1)

    model.x = pyo.Var(model.drivers, model.rides, domain=pyo.Binary)

    def obj_rule(model):
        return sum(cost_matrix[i][j] * model.x[i, j]
                   for i in model.drivers for j in model.rides)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def driver_rule(model, i):
        return sum(model.x[i, j] for j in model.rides) == 1

    model.driver_constraint = pyo.Constraint(model.drivers, rule=driver_rule)

    def ride_rule(model, j):
        return sum(model.x[i, j] for i in model.drivers) == 1

    model.ride_constraint = pyo.Constraint(model.rides, rule=ride_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
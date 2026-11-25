import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cargo_weights = params["cargo_weights"]
    vehicle_capacity = params["vehicle_capacity"]

    n_items = len(cargo_weights)
    n_vehicles = n_items  # one vehicle per item worst case

    model = pyo.ConcreteModel()

    model.ITEMS = pyo.RangeSet(0, n_items - 1)
    model.VEHICLES = pyo.RangeSet(0, n_vehicles - 1)

    model.y = pyo.Var(model.VEHICLES, domain=pyo.Binary)
    model.x = pyo.Var(model.VEHICLES, model.ITEMS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.y[v] for v in m.VEHICLES)

    model.total_vehicles = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[v, i] for v in m.VEHICLES) == 1

    model.assign_constraint = pyo.Constraint(model.ITEMS, rule=assign_rule)

    def cap_rule(m, v):
        return sum(cargo_weights[i] * m.x[v, i] for i in m.ITEMS) <= vehicle_capacity * m.y[v]

    model.capacity_constraint = pyo.Constraint(model.VEHICLES, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_vehicles))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    truck_capacity = params["truck_capacity"]
    good_weights = params["good_weights"]

    num_goods = len(good_weights)
    num_trucks = num_goods

    model = pyo.ConcreteModel()

    model.GOODS = pyo.RangeSet(0, num_goods - 1)
    model.TRUCKS = pyo.RangeSet(0, num_trucks - 1)

    model.assign = pyo.Var(model.GOODS, model.TRUCKS, domain=pyo.Binary)
    model.use_truck = pyo.Var(model.TRUCKS, domain=pyo.Binary)

    def assign_rule(m, g):
        return sum(m.assign[g, t] for t in m.TRUCKS) == 1

    model.assign_con = pyo.Constraint(model.GOODS, rule=assign_rule)

    def capacity_rule(m, t):
        return sum(good_weights[g] * m.assign[g, t] for g in m.GOODS) <= truck_capacity * m.use_truck[t]

    model.capacity_con = pyo.Constraint(model.TRUCKS, rule=capacity_rule)

    def objective_rule(m):
        return sum(m.use_truck[t] for t in m.TRUCKS)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_impressions = params["capacity_impressions"]
    capacity_cost = params["capacity_cost"]
    demand_impressions = params["demand_impressions"]
    demand_cost = params["demand_cost"]

    num_items = len(demand_impressions)
    num_slots = num_items  # sufficient inventory
    num_dims = 2

    caps = {0: capacity_impressions, 1: capacity_cost}
    weights = {}
    for idx in range(num_items):
        weights[(idx, 0)] = demand_impressions[idx]
        weights[(idx, 1)] = demand_cost[idx]

    model = pyo.ConcreteModel()

    model.item_set = pyo.RangeSet(0, num_items - 1)
    model.slot_set = pyo.RangeSet(0, num_slots - 1)
    model.dim_set = pyo.RangeSet(0, num_dims - 1)

    model.x = pyo.Var(model.item_set, model.slot_set, domain=pyo.Binary)
    model.y = pyo.Var(model.slot_set, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.y[j] for j in model.slot_set), sense=pyo.minimize
    )

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in m.slot_set) == 1
    model.assign = pyo.Constraint(model.item_set, rule=assign_rule)

    def cap_rule(m, j, d):
        return sum(weights[(i, d)] * m.x[i, j] for i in m.item_set) <= caps[d] * m.y[j]
    model.cap = pyo.Constraint(model.slot_set, model.dim_set, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
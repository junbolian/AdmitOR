import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    hubs = [0, 1, 2, 3, 4]
    demand = {
        0: params["demand_0"],
        1: params["demand_1"],
        2: -params["supply_2"],
        3: -params["supply_3"],
        4: -params["supply_4"],
    }

    pairs = [(i, j) for i in hubs for j in hubs if i != j]

    n_pairs = len(pairs)
    fixed_cost = {}
    variable_cost = {}
    capacity = {}
    for k, (i, j) in enumerate(pairs):
        t = k / max(n_pairs - 1, 1)
        fixed_cost[(i, j)] = params["fixed_cost_min"] + t * (params["fixed_cost_max"] - params["fixed_cost_min"])
        variable_cost[(i, j)] = params["variable_cost_min"] + t * (params["variable_cost_max"] - params["variable_cost_min"])
        capacity[(i, j)] = params["capacity_min"] + t * (params["capacity_max"] - params["capacity_min"])

    model = pyo.ConcreteModel()

    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.establish = pyo.Var(model.pairs, domain=pyo.Binary)
    model.ship = pyo.Var(model.pairs, domain=pyo.NonNegativeReals)

    def capacity_rule(m, i, j):
        return m.ship[i, j] <= capacity[(i, j)] * m.establish[i, j]

    model.capacity_con = pyo.Constraint(model.pairs, rule=capacity_rule)

    def balance_rule(m, h):
        inflow = sum(m.ship[i, j] for (i, j) in pairs if j == h)
        outflow = sum(m.ship[i, j] for (i, j) in pairs if i == h)
        return inflow - outflow == demand[h]

    model.balance_con = pyo.Constraint(hubs, rule=balance_rule)

    def total_cost(m):
        return sum(fixed_cost[(i, j)] * m.establish[i, j] for (i, j) in pairs) + \
               sum(variable_cost[(i, j)] * m.ship[i, j] for (i, j) in pairs)

    model.total_cost = pyo.Objective(rule=total_cost, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
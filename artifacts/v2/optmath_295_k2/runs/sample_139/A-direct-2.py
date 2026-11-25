import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    model = pyo.ConcreteModel()

    hubs = [0, 1, 2, 3, 4]
    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    net_flow = {
        0: -params["net_flow_hub0"],
        1: -params["net_flow_hub1"],
        2: params["net_flow_hub2"],
        3: -params["net_flow_hub3"],
        4: -params["net_flow_hub4"],
    }

    default_fixed = params["fixed_cost_other"]
    default_cap = params["capacity_other"]
    default_varc = params["variable_cost_other"]

    fixed_cost = {}
    capacity = {}
    varcost = {}
    for (i, j) in arcs:
        if (i, j) == (0, 1):
            fixed_cost[(i, j)] = params["fixed_cost_0_1"]
            capacity[(i, j)] = params["capacity_0_1"]
            varcost[(i, j)] = params["variable_cost_0_1"]
        elif (i, j) == (0, 2):
            fixed_cost[(i, j)] = params["fixed_cost_0_2"]
            capacity[(i, j)] = params["capacity_0_2"]
            varcost[(i, j)] = params["variable_cost_0_2"]
        else:
            fixed_cost[(i, j)] = default_fixed
            capacity[(i, j)] = default_cap
            varcost[(i, j)] = default_varc

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.HUBS = pyo.Set(initialize=hubs)

    model.y = pyo.Var(model.ARCS, within=pyo.Binary)
    model.x = pyo.Var(model.ARCS, within=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity[(i, j)] * m.y[i, j]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def balance_rule(m, k):
        outflow = sum(m.x[k, j] for j in hubs if j != k)
        inflow = sum(m.x[i, k] for i in hubs if i != k)
        return outflow - inflow == net_flow[k]
    model.balance_con = pyo.Constraint(model.HUBS, rule=balance_rule)

    def obj_rule(m):
        return sum(fixed_cost[(i, j)] * m.y[i, j] for (i, j) in arcs) + \
               sum(varcost[(i, j)] * m.x[i, j] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    ]
    nodes = [0, 1, 2, 3, 4, 5]

    supply = {
        0: params["supply_0"],
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: -params["demand_4"],
        5: -params["demand_5"],
    }

    capacity = {a: params["capacity"][k] for k, a in enumerate(arcs)}
    unit_cost = {a: params["unit_cost"][k] for k, a in enumerate(arcs)}

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.NODE = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.ARC, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= capacity[(i, j)]

    model.cap_con = pyo.Constraint(model.ARC, rule=cap_rule)

    def balance_rule(mdl, n):
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        return outflow - inflow == supply[n]

    model.balance_con = pyo.Constraint(model.NODE, rule=balance_rule)

    model.obj = pyo.Objective(
        expr=sum(unit_cost[(i, j)] * model.flow[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
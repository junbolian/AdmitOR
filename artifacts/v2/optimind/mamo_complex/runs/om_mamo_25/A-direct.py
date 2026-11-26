import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (1, 2, "capacity_1_2"),
        (1, 3, "capacity_1_3"),
        (2, 3, "capacity_2_3"),
        (2, 4, "capacity_2_4"),
        (3, 4, "capacity_3_4"),
    ]
    nodes = [1, 2, 3, 4]
    source = 1
    sink = 4

    model = pyo.ConcreteModel()

    model.E = pyo.Set(initialize=[(u, v) for (u, v, _) in edges], dimen=2)
    model.N = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.E, domain=pyo.NonNegativeReals)

    # capacity constraints
    def cap_rule(model, u, v):
        for (a, b, pname) in edges:
            if a == u and b == v:
                return model.flow[u, v] <= params[pname]
        return pyo.Constraint.Skip

    model.cap = pyo.Constraint(model.E, rule=cap_rule)

    # flow conservation
    def bal_rule(model, n):
        inflow = sum(model.flow[u, v] for (u, v) in model.E if v == n)
        outflow = sum(model.flow[u, v] for (u, v) in model.E if u == n)
        if n == source:
            return outflow - inflow >= 0
        elif n == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0

    model.bal = pyo.Constraint(model.N, rule=bal_rule)

    # maximize flow out of source (equivalently into sink)
    model.obj = pyo.Objective(
        expr=sum(model.flow[source, v] for (u, v) in model.E if u == source),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": round(obj_val), "status": "optimal"}
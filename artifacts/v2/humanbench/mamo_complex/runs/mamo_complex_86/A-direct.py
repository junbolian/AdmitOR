import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        ("1", "2", params["capacity_1_2"]),
        ("1", "3", params["capacity_1_3"]),
        ("2", "3", params["capacity_2_3"]),
        ("2", "4", params["capacity_2_4"]),
        ("3", "4", params["capacity_3_4"]),
    ]

    model = pyo.ConcreteModel()
    model.E = pyo.Set(initialize=[(u, v) for (u, v, c) in edges])
    model.cap = pyo.Param(model.E, initialize={(u, v): c for (u, v, c) in edges}, mutable=True)

    model.x = pyo.Var(model.E, domain=pyo.NonNegativeReals)
    model.flow = pyo.Var(domain=pyo.NonNegativeReals)

    def cap_rule(mdl, u, v):
        return mdl.x[(u, v)] <= mdl.cap[(u, v)]

    model.cap_con = pyo.Constraint(model.E, rule=cap_rule)

    nodes = ["1", "2", "3", "4"]
    source = "1"
    sink = "4"

    def balance_rule(mdl, n):
        inflow = sum(mdl.x[(u, v)] for (u, v) in mdl.E if v == n)
        outflow = sum(mdl.x[(u, v)] for (u, v) in mdl.E if u == n)
        if n == source:
            return outflow - inflow == mdl.flow
        elif n == sink:
            return inflow - outflow == mdl.flow
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    model.obj = pyo.Objective(expr=model.flow, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
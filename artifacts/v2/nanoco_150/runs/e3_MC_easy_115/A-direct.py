import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    cost = params["cost"]

    edges = [
        (0, 1), (0, 2), (0, 6), (0, 8), (1, 2), (1, 5), (2, 3),
        (2, 6), (3, 4), (4, 5), (5, 6), (6, 7), (6, 8), (7, 8),
    ]
    nodes = list(range(9))
    source = 0
    sink = 8

    edge_index = list(range(len(edges)))
    cap = {i: capacity[i] for i in edge_index}

    model = pyo.ConcreteModel()
    model.f = pyo.Var(edge_index, domain=pyo.NonNegativeReals)

    model.cap_con = pyo.Constraint(
        edge_index, rule=lambda m, i: m.f[i] <= cap[i])

    def flow_balance_rule(m, n):
        inflow = sum(m.f[i] for i, e in enumerate(edges) if e[1] == n)
        outflow = sum(m.f[i] for i, e in enumerate(edges) if e[0] == n)
        if n == source:
            return outflow - inflow >= 0
        if n == sink:
            return inflow - outflow >= 0
        return inflow - outflow == 0

    model.flow_balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    out_of_source = sum(model.f[i] for i, e in enumerate(edges) if e[0] == source)
    model.obj = pyo.Objective(expr=out_of_source, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
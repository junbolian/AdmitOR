import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [("1", "2"), ("1", "3"), ("2", "3"), ("2", "4"), ("3", "4")]
    cap_keys = {
        ("1", "2"): "cap_1_2",
        ("1", "3"): "cap_1_3",
        ("2", "3"): "cap_2_3",
        ("2", "4"): "cap_2_4",
        ("3", "4"): "cap_3_4",
    }
    nodes = ["1", "2", "3", "4"]
    source = "1"
    sink = "4"

    model = pyo.ConcreteModel()

    model.edges = pyo.Set(initialize=edges, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    def cap_bounds(mdl, i, j):
        return (0, params[cap_keys[(i, j)]])

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals, bounds=cap_bounds)

    # Max flow variable equals total net outflow from source
    model.maxflow = pyo.Var(domain=pyo.NonNegativeReals)

    def balance_rule(mdl, n):
        inflow = sum(mdl.flow[i, j] for (i, j) in edges if j == n)
        outflow = sum(mdl.flow[i, j] for (i, j) in edges if i == n)
        if n == source:
            return outflow - inflow == mdl.maxflow
        elif n == sink:
            return inflow - outflow == mdl.maxflow
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.obj = pyo.Objective(expr=model.maxflow, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": round(obj_val), "status": "optimal"}
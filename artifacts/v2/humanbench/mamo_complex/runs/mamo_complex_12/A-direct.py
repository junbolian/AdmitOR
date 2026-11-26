import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = ["S", "2", "3", "4", "5", "6", "7", "T"]

    edge_keys = [
        ("S", "2"), ("S", "3"),
        ("2", "S"), ("2", "4"), ("2", "3"),
        ("3", "S"), ("3", "2"), ("3", "5"), ("3", "6"),
        ("4", "2"), ("4", "6"),
        ("5", "3"), ("5", "T"),
        ("6", "3"), ("6", "4"), ("6", "7"),
        ("7", "6"), ("7", "T"),
        ("T", "5"), ("T", "7"),
    ]

    def pname(i, j):
        return "edge_" + str(i) + "_" + str(j)

    weights = {(i, j): params[pname(i, j)] for (i, j) in edge_keys}

    model.x = pyo.Var(edge_keys, domain=pyo.Binary)

    # Outflow from S must be 1
    model.flow_S = pyo.Constraint(
        expr=sum(model.x[(i, j)] for (i, j) in edge_keys if i == "S") == 1
    )

    # Inflow to T must be 1
    model.flow_T = pyo.Constraint(
        expr=sum(model.x[(i, j)] for (i, j) in edge_keys if j == "T") == 1
    )

    # Flow conservation for intermediate nodes
    inter = ["2", "3", "4", "5", "6", "7"]
    model.flow_bal = pyo.Constraint(
        inter,
        rule=lambda m, k: sum(m.x[(i, j)] for (i, j) in edge_keys if i == k)
        == sum(m.x[(i, j)] for (i, j) in edge_keys if j == k),
    )

    model.obj = pyo.Objective(
        expr=sum(weights[(i, j)] * model.x[(i, j)] for (i, j) in edge_keys),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
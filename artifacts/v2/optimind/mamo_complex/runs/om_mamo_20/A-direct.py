import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]
    n = 9

    source = 0
    sink = 8

    model = pyo.ConcreteModel()

    # Flow variables for each ordered pair with positive capacity
    arcs = [
        (i, j)
        for i in range(n)
        for j in range(n)
        if i != j and capacity_matrix[i][j] > 0
    ]

    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # Capacity constraints
    def cap_rule(model, i, j):
        return model.flow[(i, j)] <= capacity_matrix[i][j]

    model.cap_con = pyo.Constraint(model.arcs, rule=cap_rule)

    # Flow conservation for intermediate nodes
    intermediate = [k for k in range(n) if k != source and k != sink]

    def balance_rule(model, k):
        inflow = sum(model.flow[(i, k)] for i in range(n) if (i, k) in model.arcs)
        outflow = sum(model.flow[(k, j)] for j in range(n) if (k, j) in model.arcs)
        return inflow == outflow

    model.balance = pyo.Constraint(intermediate, rule=balance_rule)

    # Objective: maximize net outflow from source (equivalently inflow to sink)
    def obj_rule(model):
        outflow = sum(model.flow[(source, j)] for j in range(n) if (source, j) in model.arcs)
        inflow = sum(model.flow[(i, source)] for i in range(n) if (i, source) in model.arcs)
        return outflow - inflow

    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sectors = list(range(9))
    arcs = [(i, j) for i in sectors for j in sectors if i != j]

    model = pyo.ConcreteModel()

    model.arc_list = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arc_list, domain=pyo.NonNegativeReals)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    cap_key = {}
    for (i, j) in arcs:
        key = "cap_%d_%d" % (i, j)
        if key in params:
            cap_key[(i, j)] = "#fixed#"
    model.active_arcs = pyo.Set(initialize=[a for a in arcs if a in cap_key], dimen=2)

    def cap_rule(model, i, j):
        return model.flow[i, j] <= params["cap_%d_%d" % (i, j)]
    model.cap_constraint = pyo.Constraint(model.active_arcs, rule=cap_rule)

    def balance_rule(model, k):
        inflow = sum(model.flow[i, j] for (i, j) in model.active_arcs if j == k)
        outflow = sum(model.flow[i, j] for (i, j) in model.active_arcs if i == k)
        if k == 0:
            return outflow - inflow == model.total_flow
        elif k == 8:
            return inflow - outflow == model.total_flow
        else:
            return inflow - outflow == 0
    model.balance_constraint = pyo.Constraint(sectors, rule=balance_rule)

    model.objective_expr = pyo.Objective(expr=model.total_flow, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective_expr))
    return {"objective": obj_val, "status": "optimal"}
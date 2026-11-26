import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [0, 1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cap_keys = {
        (i, j): f"capacity_{i}_to_{j}"
        for (i, j) in arcs
    }

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        key = cap_keys[(i, j)]
        if key in params:
            return mdl.x[i, j] <= params[key]
        return pyo.Constraint.Skip

    model.capacity_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def flow_balance_rule(mdl, k):
        inflow = sum(mdl.x[i, j] for (i, j) in arcs if j == k)
        outflow = sum(mdl.x[i, j] for (i, j) in arcs if i == k)
        if k == 0:
            return inflow - outflow == -mdl.total_flow
        elif k == 5:
            return inflow - outflow == mdl.total_flow
        else:
            return inflow - outflow == 0

    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    model.flow_balance = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    model.obj = pyo.Objective(expr=model.total_flow, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
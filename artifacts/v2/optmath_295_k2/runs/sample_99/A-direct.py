import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    nodes = [0, 1, 2, 3]
    arcs = [(0, 1), (0, 2), (0, 3),
            (1, 0), (1, 2), (1, 3),
            (2, 0), (2, 1), (2, 3),
            (3, 0), (3, 1), (3, 2)]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.fixed = pyo.Param(model.A, initialize={a: fixed_cost[i] for i, a in enumerate(arcs)}, mutable=False)
    model.varcost = pyo.Param(model.A, initialize={a: variable_cost[i] for i, a in enumerate(arcs)}, mutable=False)
    model.cap = pyo.Param(model.A, initialize={a: capacity[i] for i, a in enumerate(arcs)}, mutable=False)
    model.demand = pyo.Param(model.N, initialize={n: net_demand[i] for i, n in enumerate(nodes)}, mutable=False)

    model.y = pyo.Var(model.A, domain=pyo.Binary)
    model.x = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, i, j):
        return mdl.x[i, j] <= mdl.cap[i, j] * mdl.y[i, j]
    model.capacity_con = pyo.Constraint(model.A, rule=capacity_rule)

    def balance_rule(mdl, n):
        inflow = sum(mdl.x[i, j] for (i, j) in arcs if j == n)
        outflow = sum(mdl.x[i, j] for (i, j) in arcs if i == n)
        return inflow - outflow == mdl.demand[n]
    model.balance_con = pyo.Constraint(model.N, rule=balance_rule)

    def obj_rule(mdl):
        return sum(mdl.fixed[i, j] * mdl.y[i, j] + mdl.varcost[i, j] * mdl.x[i, j] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}
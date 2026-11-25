import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)
    m = len(cost_matrix[0])

    model = pyo.ConcreteModel()

    model.TRUCK = pyo.RangeSet(n)
    model.ROUTE = pyo.RangeSet(m)

    def cost_rule(mdl, i, j):
        return cost_matrix[i - 1][j - 1]

    model.cost = pyo.Param(model.TRUCK, model.ROUTE, rule=cost_rule)

    model.x = pyo.Var(model.TRUCK, model.ROUTE, domain=pyo.Binary)

    def truck_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.ROUTE) == 1

    def route_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.TRUCK) == 1

    model.truck_con = pyo.Constraint(model.TRUCK, rule=truck_rule)
    model.route_con = pyo.Constraint(model.ROUTE, rule=route_rule)

    model.obj = pyo.Objective(
        expr=sum(model.cost[i, j] * model.x[i, j]
                 for i in model.TRUCK for j in model.ROUTE),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}
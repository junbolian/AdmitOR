import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_supply = params["net_supply"]
    cost = params["cost"]
    capacity = params["capacity"]

    n = len(net_supply)
    routes = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(routes, domain=pyo.NonNegativeReals)

    def flow_rule(mdl, j):
        inflow = sum(mdl.x[i, j] for i in range(n) if i != j)
        outflow = sum(mdl.x[j, k] for k in range(n) if k != j)
        return inflow - outflow == -net_supply[j]

    model.flow_balance = pyo.Constraint(range(n), rule=flow_rule)
    model.cap = pyo.Constraint(routes, rule=lambda mdl, i, j: mdl.x[i, j] <= capacity[i][j])

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for (i, j) in routes),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
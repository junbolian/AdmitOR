import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_warehouses = len(supply)
    n_stores = len(demand)
    warehouses = list(range(n_warehouses))
    stores = list(range(n_stores))

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses)
    model.S = pyo.Set(initialize=stores)
    model.WS = pyo.Set(initialize=[(i, j) for i in warehouses for j in stores])

    model.x = pyo.Var(model.WS, domain=pyo.NonNegativeReals)

    def supply_rule(md, i):
        return sum(md.x[i, j] for j in stores) == supply[i]
    model.supply_con = pyo.Constraint(model.W, rule=supply_rule)

    def demand_rule(md, j):
        return sum(md.x[i, j] for i in warehouses) == demand[j]
    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def cap_rule(md, i, j):
        return md.x[i, j] <= capacity[i][j]
    model.cap_con = pyo.Constraint(model.WS, rule=cap_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for (i, j) in model.WS),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_warehouses = len(supply)
    n_stores = len(demand)

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, n_warehouses - 1)
    model.S = pyo.RangeSet(0, n_stores - 1)

    model.x = pyo.Var(model.W, model.S, domain=pyo.NonNegativeReals)

    def obj_rule(mod):
        return sum(cost[i][j] * mod.x[i, j] for i in mod.W for j in mod.S)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.S) == supply[i]

    model.supply_con = pyo.Constraint(model.W, rule=supply_rule)

    def demand_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.W) == demand[j]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "no objective value"}

    return {"objective": obj_val, "status": "optimal"}
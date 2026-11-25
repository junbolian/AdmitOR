import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_warehouses = len(supply)
    num_stores = len(demand)
    warehouses = list(range(num_warehouses))
    stores = list(range(num_stores))

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses)
    model.S = pyo.Set(initialize=stores)
    model.WS = pyo.Set(initialize=[(w, s) for w in warehouses for s in stores])

    model.x = pyo.Var(model.WS, domain=pyo.NonNegativeReals)

    def cap_rule(model, w, s):
        return model.x[w, s] <= capacity[w][s]

    model.cap_con = pyo.Constraint(model.WS, rule=cap_rule)

    def supply_rule(model, w):
        return sum(model.x[w, s] for s in model.S) == supply[w]

    model.supply_con = pyo.Constraint(model.W, rule=supply_rule)

    def demand_rule(model, s):
        return sum(model.x[w, s] for w in model.W) == demand[s]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def obj_rule(model):
        return sum(cost[w][s] * model.x[w, s] for w, s in model.WS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
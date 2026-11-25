import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["warehouse_supply"]
    demand = params["store_demand"]
    cost = params["transport_cost"]
    cap = params["route_capacity"]

    nW = len(supply)
    nS = len(demand)
    W = range(nW)
    S = range(nS)

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=list(W))
    model.S = pyo.Set(initialize=list(S))

    model.x = pyo.Var(model.W, model.S, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.W for j in mdl.S)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.S) <= supply[i]
    model.supply_con = pyo.Constraint(model.W, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.W) == demand[j]
    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= cap[i][j]
    model.cap_con = pyo.Constraint(model.W, model.S, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
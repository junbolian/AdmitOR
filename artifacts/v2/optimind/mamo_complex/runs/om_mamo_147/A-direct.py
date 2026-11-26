import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["initial_supply"]
    demand = params["demand"]
    cost = params["transport_cost"]

    n = len(supply)
    regions = list(range(n))
    pairs = [(i, j) for i in regions for j in regions if i != j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in regions if j != i) <= supply[i]
    model.supply_con = pyo.Constraint(regions, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in regions if i != j) + supply[j] >= demand[j]
    model.demand_con = pyo.Constraint(regions, rule=demand_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for (i, j) in pairs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}
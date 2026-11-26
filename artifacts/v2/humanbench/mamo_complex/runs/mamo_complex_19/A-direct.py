import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    opening_costs = params["opening_costs"]
    transportation_costs = params["transportation_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    num_centers = params["num_centers"]
    num_stores = params["num_stores"]

    centers = list(range(num_centers))
    stores = list(range(num_stores))

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers)
    model.S = pyo.Set(initialize=stores)

    model.y = pyo.Var(model.C, domain=pyo.Binary)
    model.x = pyo.Var(model.C, model.S, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, c):
        return sum(mdl.x[c, s] for s in mdl.S) <= capacities[c] * mdl.y[c]
    model.supply_con = pyo.Constraint(model.C, rule=supply_rule)

    def demand_rule(mdl, s):
        return sum(mdl.x[c, s] for c in mdl.C) >= demands[s]
    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def objective_rule(mdl):
        open_cost = sum(opening_costs[c] * mdl.y[c] for c in mdl.C)
        trans_cost = sum(transportation_costs[c][s] * mdl.x[c, s] for c in mdl.C for s in mdl.S)
        return open_cost + trans_cost
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}
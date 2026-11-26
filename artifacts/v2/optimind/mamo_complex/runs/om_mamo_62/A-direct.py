import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    num_centers = params["num_centers"]
    num_stores = params["num_stores"]

    centers = list(range(num_centers))
    stores = list(range(num_stores))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(centers, domain=pyo.Binary)

    def demand_rule(md, j):
        return sum(md.x[i, j] for i in centers) == demands[j]
    model.demand_con = pyo.Constraint(stores, rule=demand_rule)

    def capacity_rule(md, i):
        return sum(md.x[i, j] for j in stores) <= capacities[i] * md.y[i]
    model.capacity_con = pyo.Constraint(centers, rule=capacity_rule)

    def transport_rule(md, i, j):
        return md.x[i, j] <= capacities[i] * md.y[i]
    model.transport_con = pyo.Constraint(centers, stores, rule=transport_rule)

    def obj_rule(md):
        return sum(opening_costs[i] * md.y[i] for i in centers) + \
               sum(transport_costs[i][j] * md.x[i, j] for i in centers for j in stores)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}
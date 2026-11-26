import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_centers = len(opening_costs)
    num_stores = len(demands)

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, num_centers - 1)
    model.S = pyo.RangeSet(0, num_stores - 1)

    model.y = pyo.Var(model.C, domain=pyo.Binary)
    model.x = pyo.Var(model.C, model.S, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(opening_costs[c] * m.y[c] for c in m.C) + \
               sum(transport_costs[c][s] * m.x[c, s] for c in m.C for s in m.S)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def demand_rule(m, s):
        return sum(m.x[c, s] for c in m.C) == demands[s]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(m, c):
        return sum(m.x[c, s] for s in m.S) <= capacities[c] * m.y[c]

    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
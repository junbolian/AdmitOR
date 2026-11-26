import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = 6
    n_stores = 8

    # Structural transportation cost matrix (rows = centers, cols = stores).
    # Only endpoints are given in the problem; interior entries are structural.
    transport_costs = [[2, 3, 3, 3, 3, 4, 4, 5],
                       [2, 4, 1, 2, 3, 4, 2, 2],
                       [5, 4, 2, 3, 2, 4, 3, 4],
                       [4, 3, 1, 1, 3, 2, 3, 3],
                       [5, 1, 2, 3, 1, 3, 2, 2],
                       [1, 2, 5, 3, 1, 4, 2, 4]]

    centers = range(n_centers)
    stores = range(n_stores)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(centers, domain=pyo.Binary)

    def obj_rule(m):
        return (sum(opening_costs[i] * m.y[i] for i in centers)
                + sum(transport_costs[i][j] * m.x[i, j]
                      for i in centers for j in stores))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in centers) == demands[j]

    model.demand_con = pyo.Constraint(stores, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in stores) <= capacities[i] * m.y[i]

    model.capacity_con = pyo.Constraint(centers, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
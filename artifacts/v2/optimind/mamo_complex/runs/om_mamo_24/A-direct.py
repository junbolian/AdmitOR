import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_centers = len(opening_costs)
    num_stores = len(demands)
    centers = range(num_centers)
    stores = range(num_stores)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(centers, domain=pyo.Binary)

    def obj_rule(m):
        return (
            sum(opening_costs[i] * m.y[i] for i in centers)
            + sum(transport_costs[i][j] * m.x[i, j] for i in centers for j in stores)
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in centers) == demands[j]

    model.demand_con = pyo.Constraint(stores, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in stores) <= capacities[i] * m.y[i]

    model.cap_con = pyo.Constraint(centers, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
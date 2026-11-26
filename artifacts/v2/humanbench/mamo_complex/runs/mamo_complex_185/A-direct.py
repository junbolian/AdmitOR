import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = len(opening_costs)
    n_stores = len(demands)

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, n_centers - 1)
    model.stores = pyo.RangeSet(0, n_stores - 1)

    model.open = pyo.Var(model.centers, domain=pyo.Binary)
    model.ship = pyo.Var(model.centers, model.stores, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        open_cost = sum(opening_costs[i] * m.open[i] for i in m.centers)
        ship_cost = sum(
            transport_costs[i][j] * m.ship[i, j]
            for i in m.centers
            for j in m.stores
        )
        return open_cost + ship_cost

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.ship[i, j] for i in m.centers) >= demands[j]

    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.ship[i, j] for j in m.stores) <= capacities[i] * m.open[i]

    model.capacity_con = pyo.Constraint(model.centers, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
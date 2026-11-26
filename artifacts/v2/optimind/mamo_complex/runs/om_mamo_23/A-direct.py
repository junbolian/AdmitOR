import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    store_demands = params["store_demands"]
    center_capacities = params["center_capacities"]

    n_centers = len(opening_costs)
    n_stores = len(store_demands)

    model = pyo.ConcreteModel()

    model.CENTERS = pyo.RangeSet(0, n_centers - 1)
    model.STORES = pyo.RangeSet(0, n_stores - 1)

    model.open = pyo.Var(model.CENTERS, within=pyo.Binary)
    model.ship = pyo.Var(model.CENTERS, model.STORES, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return (
            sum(opening_costs[i] * m.open[i] for i in m.CENTERS)
            + sum(transport_costs[i][j] * m.ship[i, j]
                  for i in m.CENTERS for j in m.STORES)
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.ship[i, j] for i in m.CENTERS) == store_demands[j]
    model.demand_con = pyo.Constraint(model.STORES, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.ship[i, j] for j in m.STORES) <= center_capacities[i] * m.open[i]
    model.capacity_con = pyo.Constraint(model.CENTERS, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    regions = range(n)

    model = pyo.ConcreteModel()

    # Decision variable: units shipped from i to j (i != j)
    model.flow = pyo.Var(regions, regions, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(
            transport_cost[i][j] * m.flow[i, j]
            for i in regions
            for j in regions
            if i != j
        )
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Supply constraint: total outgoing (excluding self) <= supply
    def supply_rule(m, i):
        return sum(m.flow[i, j] for j in regions if j != i) <= supply[i]
    model.supply_con = pyo.Constraint(regions, rule=supply_rule)

    # Demand constraint: total incoming (excluding self) >= demand
    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in regions if i != j) >= demand[j]
    model.demand_con = pyo.Constraint(regions, rule=demand_rule)

    # Disallow self-transport
    def no_self_rule(m, i):
        return m.flow[i, i] == 0
    model.no_self = pyo.Constraint(regions, rule=no_self_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
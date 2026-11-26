import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    cities = list(range(n))

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])

    # x[i, j]: tons of food transported from city i to city j
    model.x = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def obj_rule(md):
        return sum(cost[i][j] * md.x[i, j] for (i, j) in md.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city cannot ship out more than it has.
    def supply_rule(md, i):
        return sum(md.x[i, j] for j in md.cities if j != i) <= supply[i]

    model.supply_con = pyo.Constraint(model.cities, rule=supply_rule)

    # Each city must end up with at least its demand:
    # local supply + inflows - outflows >= demand
    def demand_rule(md, j):
        inflow = sum(md.x[i, j] for i in md.cities if i != j)
        outflow = sum(md.x[j, k] for k in md.cities if k != j)
        return supply[j] + inflow - outflow >= demand[j]

    model.demand_con = pyo.Constraint(model.cities, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    num_facilities = len(supply)
    num_centers = len(demand)
    facilities = range(num_facilities)
    centers = range(num_centers)

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=list(facilities))
    model.centers = pyo.Set(initialize=list(centers))

    model.x = pyo.Var(model.facilities, model.centers,
                      domain=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.centers) == supply[i]

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.facilities) == demand[j]

    model.supply_constraint = pyo.Constraint(model.facilities, rule=supply_rule)
    model.demand_constraint = pyo.Constraint(model.centers, rule=demand_rule)

    def objective_rule(m):
        return sum(cost[i][j] * m.x[i, j]
                   for i in m.facilities for j in m.centers)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
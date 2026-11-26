import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = len(opening_cost)
    n_stores = len(demand)

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, n_centers - 1)
    model.stores = pyo.RangeSet(0, n_stores - 1)

    model.x = pyo.Var(model.centers, model.stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.centers, domain=pyo.Binary)

    def objective_rule(m):
        return (
            sum(opening_cost[i] * m.y[i] for i in m.centers)
            + sum(transport_cost[i][j] * m.x[i, j]
                  for i in m.centers for j in m.stores)
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.centers) == demand[j]

    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.stores) <= capacity[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.centers, rule=capacity_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "solve_failed"}
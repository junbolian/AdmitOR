import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_centers = len(opening_cost)
    num_stores = len(demand)

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, num_centers - 1)
    model.stores = pyo.RangeSet(0, num_stores - 1)

    # Binary: open center
    model.open_center = pyo.Var(model.centers, domain=pyo.Binary)

    # Continuous flow from center to store (non-negative units)
    model.flow = pyo.Var(model.centers, model.stores, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        open_term = sum(opening_cost[i] * m.open_center[i] for i in m.centers)
        transport_term = sum(
            transport_cost[i][j] * m.flow[i, j]
            for i in m.centers
            for j in m.stores
        )
        return open_term + transport_term

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand satisfaction for each store
    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in m.centers) >= demand[j]

    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    # Capacity constraint (flow only if center is open)
    def capacity_rule(m, i):
        return sum(m.flow[i, j] for j in m.stores) <= capacity[i] * m.open_center[i]

    model.capacity_con = pyo.Constraint(model.centers, rule=capacity_rule)

    try:
        solver = Highs()
        solver.solve(model)
    except Exception:
        return {"objective": None, "status": "solver failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or no solution"}

    return {"objective": obj_val, "status": "optimal"}
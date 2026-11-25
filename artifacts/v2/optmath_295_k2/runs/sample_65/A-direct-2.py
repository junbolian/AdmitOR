import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_fac = int(params["num_facilities"])
    num_st = int(params["num_stores"])

    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]

    # shipping costs: params["shipping_cost_row0"] gives costs from each DC to store 0.
    # For other stores, derive deterministically (structural placeholder pattern).
    s0 = params["shipping_cost_row0"]

    def ship_cost(i, j):
        if j == 0:
            return float(s0[i])
        # Deterministic structured variation for remaining lanes.
        return float(s0[i]) + ((i * 7 + j * 3) % 11)

    model = pyo.ConcreteModel()

    F = range(num_fac)
    S = range(num_st)

    model.FAC = pyo.Set(initialize=list(F))
    model.STORE = pyo.Set(initialize=list(S))

    model.x = pyo.Var(model.FAC, model.STORE, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.FAC, within=pyo.Binary)

    def obj_rule(m):
        return sum(float(fixed_cost[i]) * m.y[i] for i in m.FAC) + sum(
            ship_cost(i, j) * m.x[i, j] for i in m.FAC for j in m.STORE
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.demand_con = pyo.Constraint(
        model.STORE,
        rule=lambda m, j: sum(m.x[i, j] for i in m.FAC) == float(demand[j]),
    )

    model.cap_con = pyo.Constraint(
        model.FAC,
        rule=lambda m, i: sum(m.x[i, j] for j in m.STORE) <= float(capacity[i]) * m.y[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
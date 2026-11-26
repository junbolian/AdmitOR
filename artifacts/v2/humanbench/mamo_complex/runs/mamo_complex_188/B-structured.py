# IR: {"sets":{"I":"DCs 1..6","J":"stores 1..9"},"params":{"opening_cost":"length-6 sequence from params; dollars","transport_cost":"6x9 nested sequence from params; dollars/unit","demand":"length-9 sequence from params; units","capacity":"length-6 sequence from params; units"},"variables":{"y[i]":"Binary","x[i,j]":"NonNegativeReals"},"constraints":["For each j: sum_i x[i,j] = demand[j]","For each i: sum_j x[i,j] <= capacity[i]*y[i]"],"objective":"Minimize sum_i opening_cost[i]*y[i] + sum_i,j transport_cost[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using complete, zero-based input sequences supplied in params."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.dc_set = pyo.RangeSet(1, 6)
    model.store_set = pyo.RangeSet(1, 9)

    model.opening_cost = pyo.Param(
        model.dc_set,
        initialize=lambda mdl, i: opening_cost[i - 1],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.dc_set,
        model.store_set,
        initialize=lambda mdl, i, j: transport_cost[i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.store_set,
        initialize=lambda mdl, j: demand[j - 1],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.dc_set,
        initialize=lambda mdl, i: capacity[i - 1],
        within=pyo.NonNegativeReals,
    )

    model.y = pyo.Var(model.dc_set, domain=pyo.Binary)
    model.x = pyo.Var(
        model.dc_set, model.store_set, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.dc_set) == mdl.demand[j]

    model.demand_constraints = pyo.Constraint(
        model.store_set, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.store_set)
            <= mdl.capacity[i] * mdl.y[i]
        )

    model.capacity_constraints = pyo.Constraint(
        model.dc_set, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.y[i]
                for i in model.dc_set
            )
            + sum(
                model.transport_cost[i, j] * model.x[i, j]
                for i in model.dc_set
                for j in model.store_set
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
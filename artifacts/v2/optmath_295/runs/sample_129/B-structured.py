# IR: {"sets":{"I":"0..3","J":"0..9"},"params":{"fixed_cost":"I -> nonnegative real","demand":"J -> nonnegative real","ship_cost":"I x J -> nonnegative real","capacity":"I -> nonnegative real"},"variables":{"opened[i]":"binary for i in I","shipped[i,j]":"nonnegative real for (i,j) in I x J"},"constraints":["For each j: sum_i shipped[i,j] = demand[j]","For each i: sum_j shipped[i,j] <= capacity[i] * opened[i]"],"objective":"minimize sum_i fixed_cost[i]*opened[i] + sum_i sum_j ship_cost[i,j]*shipped[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed sequences; ship_cost is a nested sequence [i][j]."""
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    ship_cost = params["ship_cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 9)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda mdl, i: fixed_cost[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.ship_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize=lambda mdl, i, j: ship_cost[i][j],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda mdl, i: capacity[i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities, model.customers, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipped[i, j] for i in mdl.facilities)
            == mdl.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipped[i, j] for j in mdl.customers)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.facilities
            )
            + sum(
                model.ship_cost[i, j] * model.shipped[i, j]
                for i in model.facilities
                for j in model.customers
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
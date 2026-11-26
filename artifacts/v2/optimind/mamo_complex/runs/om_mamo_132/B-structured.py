# IR: {"sets":{"centers":[0,1,2,3],"outlets":[0,1,2,3]},"params":{"opening_cost":"opening_cost[i], dollars; zero-based sequence","transport_cost":"transport_cost[i][j], dollars/unit; zero-based matrix","demand":"demand[j], units; zero-based sequence","capacity":"capacity[i], units; zero-based sequence"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each outlet j: sum_i shipment[i,j] == demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i][j]*shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based sequences for vectors and a nested cost matrix."""
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 3)
    model.outlets = pyo.RangeSet(0, 3)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda _, i: params["opening_cost"][i],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.outlets,
        initialize=lambda _, i, j: params["transport_cost"][i][j],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.outlets,
        initialize=lambda _, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda _, i: params["capacity"][i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.outlets, domain=pyo.NonNegativeReals
    )

    def demand_rule(_, j):
        return (
            sum(model.shipment[i, j] for i in model.centers)
            == model.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.outlets, rule=demand_rule
    )

    def capacity_rule(_, i):
        return (
            sum(model.shipment[i, j] for j in model.outlets)
            <= model.capacity[i] * model.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.outlets
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
# IR: {"sets":{"centers":"0..6","stores":"0..8"},"params":{"opening_cost":"nonnegative vector[7]","transport_cost":"nonnegative matrix[7,9]","demand":"nonnegative vector[9]","capacity":"nonnegative vector[7]"},"variables":{"opened[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["For each store j: sum_i shipment[i,j] == demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the capacitated facility-location problem using zero-based arrays."""
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 6)
    model.stores = pyo.RangeSet(0, 8)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={
            i: params["opening_cost"][i]
            for i in model.centers
        },
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): params["transport_cost"][i][j]
            for i in model.centers
            for j in model.stores
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={
            j: params["demand"][j]
            for j in model.stores
        },
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={
            i: params["capacity"][i]
            for i in model.centers
        },
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(current_model, j):
        return (
            sum(
                current_model.shipment[i, j]
                for i in current_model.centers
            )
            == current_model.demand[j]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.stores,
        rule=demand_rule,
    )

    def capacity_rule(current_model, i):
        return (
            sum(
                current_model.shipment[i, j]
                for j in current_model.stores
            )
            <= current_model.capacity[i] * current_model.opened[i]
        )

    model.capacity_limits = pyo.Constraint(
        model.centers,
        rule=capacity_rule,
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
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
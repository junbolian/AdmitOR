# IR: {"sets":{"centers":"1..6","stores":"1..8"},"params":{"opening_cost":"nonnegative vector[6]","transport_cost":"complete nonnegative matrix[6][8]; required, missing entries never inferred","demand":"nonnegative vector[8]","capacity":"nonnegative vector[6]"},"variables":{"open_dc[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i]*open_dc[i]"],"objective":"Minimize sum_i opening_cost[i]*open_dc[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Use zero-based sequences. All 48 transportation costs are required."""
    required_keys = (
        "opening_cost",
        "transport_cost",
        "demand",
        "capacity",
    )
    for key in required_keys:
        if key not in params:
            return {"objective": None, "status": "missing_" + key}

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    if opening_cost is None or demand is None or capacity is None:
        return {"objective": None, "status": "invalid_parameters"}

    if (
        len(opening_cost) != 6
        or len(demand) != 8
        or len(capacity) != 6
    ):
        return {"objective": None, "status": "invalid_parameter_dimensions"}

    # The narrative omits interior costs, so they cannot be reconstructed.
    if (
        transport_cost is None
        or len(transport_cost) != 6
        or any(row is None or len(row) != 8 for row in transport_cost)
        or any(value is None for row in transport_cost for value in row)
    ):
        return {"objective": None, "status": "incomplete_transport_cost"}

    if any(
        value is None
        for values in (opening_cost, demand, capacity)
        for value in values
    ):
        return {"objective": None, "status": "incomplete_parameters"}

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 6)
    model.stores = pyo.RangeSet(1, 8)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={i: opening_cost[i - 1] for i in model.centers},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): transport_cost[i - 1][j - 1]
            for i in model.centers
            for j in model.stores
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={j: demand[j - 1] for j in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={i: capacity[i - 1] for i in model.centers},
        within=pyo.NonNegativeReals,
    )

    model.open_dc = pyo.Var(model.centers, within=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers,
        model.stores,
        within=pyo.NonNegativeReals,
    )

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.centers)
            == model.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.stores,
        rule=demand_rule,
    )

    def capacity_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.stores)
            <= model.capacity[i] * model.open_dc[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.open_dc[i]
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

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve can raise when no solution can be loaded.
        solver_failed = True

    # Objective retrieval alone determines success.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solver_failed" if solver_failed else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}
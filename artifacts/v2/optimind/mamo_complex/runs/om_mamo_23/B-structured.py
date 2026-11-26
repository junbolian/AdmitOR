# IR: {"sets":{"centers":[1,2,3,4],"stores":[1,2,3,4]},"params":{"opening_costs":"opening_costs[i-1]","transport_costs":"transport_costs[i-1][j-1]","store_demands":"store_demands[j-1]","center_capacities":"center_capacities[i-1]"},"variables":{"open_center[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["sum_i shipment[i,j] == store_demands[j-1] for each store j","sum_j shipment[i,j] <= center_capacities[i-1] * open_center[i] for each center i"],"objective":"minimize sum_i opening_costs[i-1]*open_center[i] + sum_i,j transport_costs[i-1][j-1]*shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using four-element vectors and a 4-by-4 transport-cost matrix."""
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    store_demands = params["store_demands"]
    center_capacities = params["center_capacities"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 4)
    model.stores = pyo.RangeSet(1, 4)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={i: opening_costs[i - 1] for i in model.centers},
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): transport_costs[i - 1][j - 1]
            for i in model.centers
            for j in model.stores
        },
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: store_demands[j - 1] for j in model.stores},
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={i: center_capacities[i - 1] for i in model.centers},
    )

    model.open_center = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.centers)
            == instance.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            <= instance.center_capacity[i] * instance.open_center[i]
        )

    model.capacity_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.open_center[i]
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

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi HiGHS can raise when no feasible solution can be loaded.
        # Success is still determined exclusively by objective retrieval.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}
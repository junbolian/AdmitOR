# IR: {"sets":{"centers":[1,2,3,4],"stores":[1,2,3,4]},"params":{"opening_costs":"center-indexed dollars","transport_costs":"center-by-store dollars/unit","demands":"store-indexed units","capacities":"center-indexed units"},"variables":{"opened[i]":"binary","shipments[i,j]":"continuous nonnegative"},"constraints":["For each store j: sum_i shipments[i,j] = demands[j]","For each center i: sum_j shipments[i,j] <= capacities[i] * opened[i]"],"objective":"Minimize sum_i opening_costs[i]*opened[i] + sum_i,j transport_costs[i,j]*shipments[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using length-four sequences and a 4-by-4 transportation matrix."""
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

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
        initialize={j: demands[j - 1] for j in model.stores},
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={i: capacities[i - 1] for i in model.centers},
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipments = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipments[i, j] for i in instance.centers)
            == instance.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(instance, i):
        return (
            sum(instance.shipments[i, j] for j in instance.stores)
            <= instance.center_capacity[i] * instance.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[i] * model.opened[i]
            for i in model.centers
        )
        + sum(
            model.transport_cost[i, j] * model.shipments[i, j]
            for i in model.centers
            for j in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
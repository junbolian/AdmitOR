# IR: {"sets":{"centers":"0..7","stores":"0..7"},"params":{"opening_costs":"params['opening_costs'][i]","transport_costs":"params['transport_costs'][i][j]","demands":"params['demands'][j]","capacities":"params['capacities'][i]"},"variables":{"opened[i]":"binary","shipment[i,j]":"continuous nonnegative"},"constraints":["For each store j: sum_i shipment[i,j] = demands[j].","For each center i: sum_j shipment[i,j] <= capacities[i] * opened[i]."],"objective":"Minimize sum_i opening_costs[i]*opened[i] + sum_i,j transport_costs[i][j]*shipment[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based sequences for the four input parameters."""
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 7)
    model.stores = pyo.RangeSet(0, 7)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={i: opening_costs[i] for i in model.centers},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): transport_costs[i][j]
            for i in model.centers
            for j in model.stores
        },
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demands[j] for j in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={i: capacities[i] for i in model.centers},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.centers)
            == instance.store_demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            <= instance.center_capacity[i] * instance.opened[i]
        )

    model.capacity_constraints = pyo.Constraint(
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
                for j in model.stores
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
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
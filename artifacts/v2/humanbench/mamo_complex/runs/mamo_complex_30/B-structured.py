# IR: {"sets":{"centers":[1,2,3,4],"stores":[1,2,3,4,5,6]},"params":{"opening_costs":"params['opening_costs'][i-1]","transport_costs":"params['transport_costs'][i-1][j-1]","demands":"params['demands'][j-1]","capacities":"params['capacities'][i-1]"},"variables":{"center_open[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":{"demand_fulfillment[j]":"sum_i shipment[i,j] == demands[j]","capacity_limit[i]":"sum_j shipment[i,j] <= capacities[i]*center_open[i]"},"objective":{"sense":"minimize","expression":"sum_i opening_costs[i]*center_open[i] + sum_i sum_j transport_costs[i,j]*shipment[i,j]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using four-entry center arrays and a 4-by-6 cost matrix."""
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(1, 4)
    model.stores = pyo.RangeSet(1, 6)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: opening_costs[i - 1],
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, i, j: transport_costs[i - 1][j - 1],
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demands[j - 1],
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: capacities[i - 1],
        within=pyo.NonNegativeReals,
    )

    model.center_open = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.centers)
            == mdl.store_demand[j]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            <= mdl.center_capacity[i] * mdl.center_open[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.center_open[i]
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
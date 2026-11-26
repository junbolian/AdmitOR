# IR: {"sets":{"I":"range(num_centers)","J":"range(num_stores)"},"params":{"num_centers":"params['num_centers']","num_stores":"params['num_stores']","opening_costs":"params['opening_costs'][i]","transport_costs":"params['transport_costs'][i][j]","demands":"params['demands'][j]","capacities":"params['capacities'][i]"},"variables":{"opened[i]":"binary","shipment[i,j]":"continuous nonnegative"},"constraints":["sum(shipment[i,j] for i in I) == demands[j] for each j in J","sum(shipment[i,j] for j in J) <= capacities[i]*opened[i] for each i in I"],"objective":"minimize sum(opening_costs[i]*opened[i] for i in I) + sum(transport_costs[i][j]*shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_centers = params["num_centers"]
    num_stores = params["num_stores"]
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=range(num_centers), ordered=True)
    model.stores = pyo.Set(initialize=range(num_stores), ordered=True)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={i: opening_costs[i] for i in range(num_centers)},
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): transport_costs[i][j]
            for i in range(num_centers)
            for j in range(num_stores)
        },
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demands[j] for j in range(num_stores)},
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={i: capacities[i] for i in range(num_centers)},
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

    model.demand_fulfillment = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            <= instance.center_capacity[i] * instance.opened[i]
        )

    model.capacity_link = pyo.Constraint(
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
        # Infeasible solves may raise because no solution can be loaded.
        # Objective retrieval below is the sole success check.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
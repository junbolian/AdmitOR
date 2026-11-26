# IR: {"sets":{"R":[0,1,2,3,4],"A":"{(i,j) in R x R: i != j}"},"params":{"supply":"params['supply'][i] for i in R","demand":"params['demand'][i] for i in R","transport_cost":"params['transport_cost'][i][j] for (i,j) in A"},"variables":{"shipment[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["For each i in R: supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i]"],"objective":"Minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept length-five supply/demand arrays and a 5-by-5 cost matrix."""
    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, 4)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.regions
            for destination in model.regions
            if origin != destination
        ],
    )

    model.supply = pyo.Param(
        model.regions,
        initialize={region: supply_data[region] for region in model.regions},
    )
    model.demand = pyo.Param(
        model.regions,
        initialize={region: demand_data[region] for region in model.regions},
    )
    model.transport_cost = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): cost_data[origin][destination]
            for origin, destination in model.routes
        },
    )

    model.shipment = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def demand_balance_rule(instance, region):
        incoming = sum(
            instance.shipment[other, region]
            for other in instance.regions
            if other != region
        )
        outgoing = sum(
            instance.shipment[region, other]
            for other in instance.regions
            if other != region
        )
        return (
            instance.supply[region] + incoming - outgoing
            >= instance.demand[region]
        )

    model.demand_balance = pyo.Constraint(
        model.regions, rule=demand_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.routes
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
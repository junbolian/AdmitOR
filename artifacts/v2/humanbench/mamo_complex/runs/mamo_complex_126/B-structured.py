# IR: {"sets":{"regions":[0,1,2,3,4,5,6],"arcs":"all ordered pairs (i,j) of distinct regions"},"params":{"supply":"params['supply'][i], nonnegative","demand":"params['demand'][i], nonnegative","transport_cost":"params['transport_cost'][i][j], real; diagonal unused"},"variables":{"shipment[i,j]":"nonnegative continuous for each arc; received supplies may be forwarded"},"constraints":["For each region i: supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i]."],"objective":"Minimize sum(transport_cost[i,j] * shipment[i,j] for all arcs)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.regions = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(7)
            for destination in range(7)
            if origin != destination
        ],
    )

    model.supply = pyo.Param(
        model.regions,
        initialize=lambda mdl, region: params["supply"][region],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.regions,
        initialize=lambda mdl, region: params["demand"][region],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, origin, destination: (
            params["transport_cost"][origin][destination]
        ),
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def regional_balance_rule(mdl, region):
        incoming = sum(
            mdl.shipment[other, region]
            for other in mdl.regions
            if other != region
        )
        outgoing = sum(
            mdl.shipment[region, other]
            for other in mdl.regions
            if other != region
        )
        return (
            mdl.supply[region] + incoming - outgoing
            >= mdl.demand[region]
        )

    model.regional_balance = pyo.Constraint(
        model.regions, rule=regional_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
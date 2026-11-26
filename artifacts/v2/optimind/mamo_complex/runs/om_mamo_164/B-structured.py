# IR: {"sets":{"R":[1,2,3,4,5],"A":"{(i,j) in R x R: i != j}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A","supply[i]":"params[f'supply_{i}'] for i in R","demand[i]":"params[f'demand_{i}'] for i in R"},"variables":{"move[i,j]":"NonNegativeIntegers for (i,j) in A"},"constraints":["supply[i] + sum(move[j,i] for j != i) - sum(move[i,j] for j != i) >= demand[i] for i in R"],"objective":"minimize sum(cost[i,j] * move[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.regions = pyo.Set(initialize=range(1, 6), ordered=True)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.regions
            for destination in model.regions
            if origin != destination
        ],
        ordered=True,
    )

    model.move_cost = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in model.routes
        },
        within=pyo.Reals,
    )
    model.available_cars = pyo.Param(
        model.regions,
        initialize={
            region: params[f"supply_{region}"]
            for region in model.regions
        },
        within=pyo.NonNegativeIntegers,
    )
    model.required_cars = pyo.Param(
        model.regions,
        initialize={
            region: params[f"demand_{region}"]
            for region in model.regions
        },
        within=pyo.NonNegativeIntegers,
    )

    model.move = pyo.Var(model.routes, domain=pyo.NonNegativeIntegers)

    def harvest_requirement_rule(model, region):
        incoming = sum(
            model.move[other, region]
            for other in model.regions
            if other != region
        )
        outgoing = sum(
            model.move[region, other]
            for other in model.regions
            if other != region
        )
        return (
            model.available_cars[region] + incoming - outgoing
            >= model.required_cars[region]
        )

    model.harvest_requirement = pyo.Constraint(
        model.regions,
        rule=harvest_requirement_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.move_cost[origin, destination]
            * model.move[origin, destination]
            for origin, destination in model.routes
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
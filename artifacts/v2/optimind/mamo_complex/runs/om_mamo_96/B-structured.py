# IR: {"sets":{"cities":[0,1,2,3,4],"arcs":"(i,j) in cities x cities where i != j"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][i]","cost":"params['cost'][i][j]"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in arcs"},"constraints":["For each city i: supply[i] + sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) >= demand[i]"],"objective":"Minimize sum(cost[i,j] * flow[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the redistribution problem using zero-based input sequences."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )

    model.initial_supply = pyo.Param(
        model.cities,
        initialize={i: supply[i] for i in model.cities},
    )
    model.required_demand = pyo.Param(
        model.cities,
        initialize={i: demand[i] for i in model.cities},
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize={(i, j): cost[i][j] for i, j in model.arcs},
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def resource_balance_rule(current_model, i):
        incoming = sum(
            current_model.flow[j, i]
            for j in current_model.cities
            if j != i
        )
        outgoing = sum(
            current_model.flow[i, j]
            for j in current_model.cities
            if j != i
        )
        return (
            current_model.initial_supply[i] + incoming - outgoing
            >= current_model.required_demand[i]
        )

    model.resource_balance = pyo.Constraint(
        model.cities,
        rule=resource_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
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
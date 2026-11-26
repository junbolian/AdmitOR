# IR: {"sets":{"D":[1,2,3,4],"A":"{(i,j): i,j in D and i != j}"},"params":{"supply":"params['supply'], length-4 array","demand":"params['demand'], length-4 array","cost":"params['cost'], four rows with either four columns or three off-diagonal columns in district order"},"variables":{"shipment[i,j]":"continuous nonnegative, (i,j) in A"},"constraints":["supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i], for each i in D"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    if len(supply) != 4 or len(demand) != 4 or len(cost) != 4:
        raise ValueError("Supply, demand, and cost must each contain four rows or entries.")

    districts = range(1, 5)
    arcs = [(origin, destination)
            for origin in districts
            for destination in districts
            if origin != destination]

    transport_cost = {}
    for origin in districts:
        row = cost[origin - 1]
        if len(row) not in (3, 4):
            raise ValueError("Each cost row must contain three or four entries.")

        for destination in districts:
            if origin == destination:
                continue
            if len(row) == 4:
                column = destination - 1
            else:
                column = destination - 1 if destination < origin else destination - 2
            transport_cost[origin, destination] = row[column]

    model = pyo.ConcreteModel()
    model.districts = pyo.Set(initialize=districts, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.available_supply = pyo.Param(
        model.districts,
        initialize={district: supply[district - 1] for district in districts},
        within=pyo.NonNegativeReals,
    )
    model.required_food = pyo.Param(
        model.districts,
        initialize={district: demand[district - 1] for district in districts},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize=transport_cost,
        within=pyo.NonNegativeReals,
    )
    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def food_balance_rule(block, district):
        incoming = sum(
            block.shipment[other, district]
            for other in block.districts
            if other != district
        )
        outgoing = sum(
            block.shipment[district, other]
            for other in block.districts
            if other != district
        )
        return (
            block.available_supply[district] + incoming - outgoing
            >= block.required_food[district]
        )

    model.food_balance = pyo.Constraint(
        model.districts, rule=food_balance_rule
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
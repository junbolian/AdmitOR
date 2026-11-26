# IR: {"sets":{"cities":[0,1,2,3,4,5],"arcs":"(i,j) in cities x cities with i != j"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][i]","cost":"params['cost'][i][j]"},"variables":{"shipment[i,j]":"continuous, nonnegative, for each arc"},"constraints":["For each city i: supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i]."],"objective":"Minimize sum(cost[i,j] * shipment[i,j] for all arcs)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the six-city food redistribution problem using zero-based inputs."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )

    model.food_supply = pyo.Param(
        model.cities,
        initialize=lambda mdl, city: supply[city],
        within=pyo.NonNegativeReals,
    )
    model.food_demand = pyo.Param(
        model.cities,
        initialize=lambda mdl, city: demand[city],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, origin, destination: cost[origin][destination],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def food_balance_rule(mdl, city):
        incoming = sum(
            mdl.shipment[other, city]
            for other in mdl.cities
            if other != city
        )
        outgoing = sum(
            mdl.shipment[city, other]
            for other in mdl.cities
            if other != city
        )
        return (
            mdl.food_supply[city] + incoming - outgoing
            >= mdl.food_demand[city]
        )

    model.food_balance = pyo.Constraint(
        model.cities,
        rule=food_balance_rule,
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
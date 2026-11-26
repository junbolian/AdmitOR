# IR: {"sets":{"cities":[0,1,2,3,4,5],"arcs":"ordered (i,j) in cities x cities with i != j"},"params":{"supply":"params['supply'][i], nonnegative tons","demand":"params['demand'][i], nonnegative tons","cost":"params['cost'][i][j], real unit transportation cost"},"variables":{"shipment[i,j]":"nonnegative continuous tons for each arc"},"constraints":["For each city i: supply[i] + sum(shipment[j,i] for j != i) - sum(shipment[i,j] for j != i) >= demand[i]."],"objective":"Minimize sum(cost[i,j] * shipment[i,j] for all arcs)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using six-element supply/demand arrays and a 6-by-6 cost matrix."""
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

    model.supply = pyo.Param(
        model.cities,
        initialize={
            city: params["supply"][city]
            for city in model.cities
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.cities,
        initialize={
            city: params["demand"][city]
            for city in model.cities
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params["cost"][origin][destination]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def food_balance_rule(instance, city):
        incoming = sum(
            instance.shipment[other, city]
            for other in instance.cities
            if other != city
        )
        outgoing = sum(
            instance.shipment[city, other]
            for other in instance.cities
            if other != city
        )
        return (
            instance.supply[city] + incoming - outgoing
            >= instance.demand[city]
        )

    model.food_balance = pyo.Constraint(
        model.cities,
        rule=food_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination]
            * model.shipment[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
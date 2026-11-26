# IR: {"sets":{"yards":["A","B"],"areas":[1,2,3]},"params":["supply_A_min","supply_B_min","demand_1","demand_2","demand_3","distance_A1","distance_A2","distance_A3","distance_B1","distance_B2","distance_B3"],"variables":{"shipment[yard,area]":"nonnegative continuous"},"constraints":["sum(shipment[A,area] for area in areas) >= supply_A_min","sum(shipment[B,area] for area in areas) >= supply_B_min","sum(shipment[yard,area] for yard in yards) == demand_area for each area"],"objective":"minimize sum(distance_yard_area * shipment[yard,area] for yard in yards for area in areas)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.yards = pyo.Set(initialize=["A", "B"], ordered=True)
    model.areas = pyo.Set(initialize=[1, 2, 3], ordered=True)

    model.minimum_supply = pyo.Param(
        model.yards,
        initialize={
            "A": params["supply_A_min"],
            "B": params["supply_B_min"],
        },
    )
    model.area_demand = pyo.Param(
        model.areas,
        initialize={
            1: params["demand_1"],
            2: params["demand_2"],
            3: params["demand_3"],
        },
    )
    model.route_distance = pyo.Param(
        model.yards,
        model.areas,
        initialize={
            ("A", 1): params["distance_A1"],
            ("A", 2): params["distance_A2"],
            ("A", 3): params["distance_A3"],
            ("B", 1): params["distance_B1"],
            ("B", 2): params["distance_B2"],
            ("B", 3): params["distance_B3"],
        },
    )

    model.shipment = pyo.Var(
        model.yards, model.areas, domain=pyo.NonNegativeReals
    )

    def minimum_supply_rule(model, yard):
        return (
            sum(model.shipment[yard, area] for area in model.areas)
            >= model.minimum_supply[yard]
        )

    model.supply_constraints = pyo.Constraint(
        model.yards, rule=minimum_supply_rule
    )

    def demand_rule(model, area):
        return (
            sum(model.shipment[yard, area] for yard in model.yards)
            == model.area_demand[area]
        )

    model.demand_constraints = pyo.Constraint(
        model.areas, rule=demand_rule
    )

    model.transport_objective = pyo.Objective(
        expr=sum(
            model.route_distance[yard, area] * model.shipment[yard, area]
            for yard in model.yards
            for area in model.areas
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.transport_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"crews":[1,2,3],"zones":[1,2,3,4,5,6,7]},"params":{"crew_capacities":"capacity[crew], supplied as a length-3 sequence","fuel_costs":"fuel[crew,zone], supplied as a 3x7 sequence of rows","operating_costs":"cost[crew,zone], supplied as a 3x7 sequence of rows"},"variables":{"assignment[crew,zone]":"Binary; 1 iff the zone is assigned to the crew"},"constraints":["For each zone: sum(assignment[crew,zone] for crew in crews) == 1","For each crew: sum(fuel[crew,zone]*assignment[crew,zone] for zone in zones) <= capacity[crew]"],"objective":"Minimize sum(cost[crew,zone]*assignment[crew,zone] for crew in crews for zone in zones)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    crew_capacities = params["crew_capacities"]
    fuel_costs = params["fuel_costs"]
    operating_costs = params["operating_costs"]

    model = pyo.ConcreteModel()

    model.crews = pyo.RangeSet(1, 3)
    model.zones = pyo.RangeSet(1, 7)

    model.capacity = pyo.Param(
        model.crews,
        initialize={
            crew: crew_capacities[crew - 1]
            for crew in model.crews
        },
    )
    model.fuel = pyo.Param(
        model.crews,
        model.zones,
        initialize={
            (crew, zone): fuel_costs[crew - 1][zone - 1]
            for crew in model.crews
            for zone in model.zones
        },
    )
    model.cost = pyo.Param(
        model.crews,
        model.zones,
        initialize={
            (crew, zone): operating_costs[crew - 1][zone - 1]
            for crew in model.crews
            for zone in model.zones
        },
    )

    model.assignment = pyo.Var(
        model.crews,
        model.zones,
        domain=pyo.Binary,
    )

    def assign_zone_rule(instance, zone):
        return sum(
            instance.assignment[crew, zone]
            for crew in instance.crews
        ) == 1

    model.assign_zone = pyo.Constraint(
        model.zones,
        rule=assign_zone_rule,
    )

    def crew_capacity_rule(instance, crew):
        return sum(
            instance.fuel[crew, zone] * instance.assignment[crew, zone]
            for zone in instance.zones
        ) <= instance.capacity[crew]

    model.crew_capacity = pyo.Constraint(
        model.crews,
        rule=crew_capacity_rule,
    )

    model.total_operating_cost = pyo.Objective(
        expr=sum(
            model.cost[crew, zone] * model.assignment[crew, zone]
            for crew in model.crews
            for zone in model.zones
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_operating_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
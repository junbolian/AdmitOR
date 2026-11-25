import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    plane0_capacity = params["plane0_capacity"]
    plane1_capacity = params["plane1_capacity"]
    plane0_cost = params["plane0_cost"]
    plane1_cost = params["plane1_cost"]
    initial_planes_per_type = params["initial_planes_per_type"]
    demand_period1 = params["demand_period1"]
    max_trips_plane0 = params["max_trips_plane0"]
    max_trips_plane1 = params["max_trips_plane1"]

    locations = [0, 1]
    plane_types = [0, 1]

    model = pyo.ConcreteModel()

    # Decision variables: trips from Location 1 to Location 0 for each plane type
    model.x = pyo.Var(plane_types, domain=pyo.NonNegativeIntegers)

    # Initial idle planes at each location for each type: distribution is not specified,
    # so it is a decision variable bounded by the total idle planes per type.
    model.init0 = pyo.Var(locations, domain=pyo.NonNegativeIntegers)
    model.init1 = pyo.Var(locations, domain=pyo.NonNegativeIntegers)

    # End-of-period idle planes at each location for each type
    model.final0 = pyo.Var(locations, domain=pyo.NonNegativeIntegers)
    model.final1 = pyo.Var(locations, domain=pyo.NonNegativeIntegers)

    # Objective: minimize total inter-location trip cost
    model.total_cost = pyo.Objective(
        expr=plane0_cost * model.x[0] + plane1_cost * model.x[1],
        sense=pyo.minimize,
    )

    # Total idle planes of each type cannot exceed the available total
    model.cap0 = pyo.Constraint(
        expr=model.init0[0] + model.init0[1] <= initial_planes_per_type
    )
    model.cap1 = pyo.Constraint(
        expr=model.init1[0] + model.init1[1] <= initial_planes_per_type
    )

    # Flow balance: idle planes at start equal idle planes at end adjusted by
    # planes arriving/departing on the Location 1 -> Location 0 route.
    # Location 0: starting idle planes plus arrivals equals ending idle planes.
    model.bal0_loc0 = pyo.Constraint(
        expr=model.final0[0] == model.init0[0] + model.x[0]
    )
    model.bal1_loc0 = pyo.Constraint(
        expr=model.final1[0] == model.init1[0] + model.x[1]
    )
    # Location 1: starting idle planes minus departures equals ending idle planes.
    model.bal0_loc1 = pyo.Constraint(
        expr=model.final0[1] == model.init0[1] - model.x[0]
    )
    model.bal1_loc1 = pyo.Constraint(
        expr=model.final1[1] == model.init1[1] - model.x[1]
    )

    # Demand satisfaction across all planes on Location 1 -> Location 0
    model.demand = pyo.Constraint(
        expr=plane0_capacity * model.x[0] + plane1_capacity * model.x[1]
        >= demand_period1
    )

    # Route restrictions: maximum trips per plane type on Location 1 -> Location 0
    model.max0 = pyo.Constraint(expr=model.x[0] <= max_trips_plane0)
    model.max1 = pyo.Constraint(expr=model.x[1] <= max_trips_plane1)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
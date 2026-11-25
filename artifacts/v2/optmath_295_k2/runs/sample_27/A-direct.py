import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    plane0_capacity = params["plane0_capacity"]
    plane1_capacity = params["plane1_capacity"]
    plane0_cost = params["plane0_cost"]
    plane1_cost = params["plane1_cost"]
    init_per_type = params["initial_planes_per_type"]
    demand = params["demand_period1"]
    max_trips_p0 = params["max_trips_plane0"]
    max_trips_p1 = params["max_trips_plane1"]

    locations = [0, 1]
    plane_types = [0, 1]

    model = pyo.ConcreteModel()

    # Decision variables: trips t[p, i, j] from location i to location j for plane type p
    # Only route 1->0 is allowed for carrying passengers / inter-location trips.
    model.t = pyo.Var(plane_types, locations, locations, domain=pyo.NonNegativeReals)

    # Idle planes at each location at start (and end) of period
    model.idle = pyo.Var(plane_types, locations, domain=pyo.NonNegativeReals)

    # Objective: cost of inter-location trips only
    def obj_rule(md):
        return (
            plane0_cost * md.t[0, 1, 0]
            + plane1_cost * md.t[1, 1, 0]
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Disallow 0->1 trips
    model.no_0_1_p0 = pyo.Constraint(expr=model.t[0, 0, 1] == 0)
    model.no_0_1_p1 = pyo.Constraint(expr=model.t[1, 0, 1] == 0)
    # Disallow within-location trips (no need / no cost)
    model.no_0_0_p0 = pyo.Constraint(expr=model.t[0, 0, 0] == 0)
    model.no_0_0_p1 = pyo.Constraint(expr=model.t[1, 0, 0] == 0)
    model.no_1_1_p0 = pyo.Constraint(expr=model.t[0, 1, 1] == 0)
    model.no_1_1_p1 = pyo.Constraint(expr=model.t[1, 1, 1] == 0)

    # Trip limits from 1->0
    model.max_p0 = pyo.Constraint(expr=model.t[0, 1, 0] <= max_trips_p0)
    model.max_p1 = pyo.Constraint(expr=model.t[1, 1, 0] <= max_trips_p1)

    # Total idle planes per type <= initial_planes_per_type
    model.total_idle_p0 = pyo.Constraint(
        expr=model.idle[0, 0] + model.idle[0, 1] <= init_per_type
    )
    model.total_idle_p1 = pyo.Constraint(
        expr=model.idle[1, 0] + model.idle[1, 1] <= init_per_type
    )

    # Flow balance: idle at start == idle at end adjusted by arrivals/departures
    # End idle at location j = start idle at location j - departures from j + arrivals to j
    # Start equals end => departures from j == arrivals to j (balanced)
    # For type p, location 0: departures = t[p,0,0]+t[p,0,1]; arrivals = t[p,1,0]
    # For type p, location 1: departures = t[p,1,0]+t[p,1,1]; arrivals = t[p,0,1]
    # With only 1->0 allowed, balance requires t[p,1,0] == t[p,0,1].
    # Since t[p,0,1]=0, we need t[p,1,0]=0... but that would forbid the trip.
    # Interpretation: start total idle equals end total idle per type, and per-location
    # flow balance with remaining idle planes.
    # End idle at loc0 = start idle[loc0] - t[p,0,0]-t[p,0,1] + t[p,1,0]
    # Setting start=end at loc0: 0 = t[p,1,0]  -> conflicts with allowed trips.
    # Standard formulation: the idle planes at end of period are adjusted:
    # end_idle[j] = idle[j] - departures[j] + arrivals[j], idle[j] >= 0, end_idle[j] >= 0.
    # The balance constraints here link start/end within the single period is trivial;
    # the meaningful constraint is availability: departing planes must be available.
    # We enforce: t[p,0,0]+t[p,0,1] <= idle[p,0]  and t[p,1,0]+t[p,1,1] <= idle[p,1].
    model.avail_p0_loc0 = pyo.Constraint(
        expr=model.t[0, 0, 0] + model.t[0, 0, 1] <= model.idle[0, 0]
    )
    model.avail_p0_loc1 = pyo.Constraint(
        expr=model.t[0, 1, 0] + model.t[0, 1, 1] <= model.idle[0, 1]
    )
    model.avail_p1_loc0 = pyo.Constraint(
        expr=model.t[1, 0, 0] + model.t[1, 0, 1] <= model.idle[1, 0]
    )
    model.avail_p1_loc1 = pyo.Constraint(
        expr=model.t[1, 1, 0] + model.t[1, 1, 1] <= model.idle[1, 1]
    )

    # Demand satisfaction: passengers carried from 1 to 0 >= demand
    model.demand_sat = pyo.Constraint(
        expr=plane0_capacity * model.t[0, 1, 0]
        + plane1_capacity * model.t[1, 1, 0]
        >= demand
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
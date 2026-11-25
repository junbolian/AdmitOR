# IR: {"sets":{"K":[0,1],"L":[0,1],"T":[0,1]},"params":{"capacity":["plane0_capacity","plane1_capacity"],"trip_cost":["plane0_trip_cost","plane1_trip_cost"],"same_loc_cost":["plane0_same_loc_cost","plane1_same_loc_cost"],"initial_idle":["initial_idle_plane0","initial_idle_plane1"],"max_idle":["max_idle_plane0","max_idle_plane1"],"demand":"demand_1_to_0","max_trips_1to0":["max_trips_plane0_1to0","max_trips_plane1_1to0"]},"variables":{"idle[t,k,l]":"nonnegative integer; t=0 start, t=1 end; initial location distribution is chosen","trips[k,i,j]":"nonnegative integer; trips during the single period"},"constraints":["sum_l idle[0,k,l] = initial_idle[k] for each k","sum_l idle[t,k,l] <= max_idle[k] for each t,k","sum_j trips[k,i,j] <= idle[0,k,i] for each k,i (each plane can depart at most once during the period)","idle[1,k,l] = idle[0,k,l] + sum_i trips[k,i,l] - sum_j trips[k,l,j] for each k,l","sum_k capacity[k]*trips[k,1,0] >= demand","trips[k,0,1] = 0 for each k","trips[k,1,0] <= max_trips_1to0[k] for each k"],"objective":"minimize sum_{k,i,j} (same_loc_cost[k] if i=j else trip_cost[k])*trips[k,i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = {
        0: params["plane0_capacity"],
        1: params["plane1_capacity"],
    }
    trip_cost = {
        0: params["plane0_trip_cost"],
        1: params["plane1_trip_cost"],
    }
    same_loc_cost = {
        0: params["plane0_same_loc_cost"],
        1: params["plane1_same_loc_cost"],
    }
    initial_idle = {
        0: params["initial_idle_plane0"],
        1: params["initial_idle_plane1"],
    }
    max_idle = {
        0: params["max_idle_plane0"],
        1: params["max_idle_plane1"],
    }
    demand = params["demand_1_to_0"]
    max_trips_1to0 = {
        0: params["max_trips_plane0_1to0"],
        1: params["max_trips_plane1_1to0"],
    }

    model = pyo.ConcreteModel()
    model.K = pyo.Set(initialize=[0, 1], ordered=True)
    model.L = pyo.Set(initialize=[0, 1], ordered=True)
    model.T = pyo.Set(initialize=[0, 1], ordered=True)

    model.idle = pyo.Var(
        model.T, model.K, model.L, domain=pyo.NonNegativeIntegers
    )
    model.trips = pyo.Var(
        model.K, model.L, model.L, domain=pyo.NonNegativeIntegers
    )

    def initial_fleet_rule(block, kind):
        return (
            sum(block.idle[0, kind, loc] for loc in block.L)
            == initial_idle[kind]
        )

    model.initial_fleet = pyo.Constraint(
        model.K, rule=initial_fleet_rule
    )

    def idle_limit_rule(block, time, kind):
        return (
            sum(block.idle[time, kind, loc] for loc in block.L)
            <= max_idle[kind]
        )

    model.idle_limit = pyo.Constraint(
        model.T, model.K, rule=idle_limit_rule
    )

    def departure_limit_rule(block, kind, origin):
        return (
            sum(block.trips[kind, origin, dest] for dest in block.L)
            <= block.idle[0, kind, origin]
        )

    model.departure_limit = pyo.Constraint(
        model.K, model.L, rule=departure_limit_rule
    )

    def flow_balance_rule(block, kind, loc):
        return block.idle[1, kind, loc] == (
            block.idle[0, kind, loc]
            + sum(block.trips[kind, origin, loc] for origin in block.L)
            - sum(block.trips[kind, loc, dest] for dest in block.L)
        )

    model.flow_balance = pyo.Constraint(
        model.K, model.L, rule=flow_balance_rule
    )

    model.demand_requirement = pyo.Constraint(
        expr=sum(
            capacity[kind] * model.trips[kind, 1, 0]
            for kind in model.K
        ) >= demand
    )

    def prohibited_route_rule(block, kind):
        return block.trips[kind, 0, 1] == 0

    model.prohibited_route = pyo.Constraint(
        model.K, rule=prohibited_route_rule
    )

    def route_limit_rule(block, kind):
        return block.trips[kind, 1, 0] <= max_trips_1to0[kind]

    model.route_limit = pyo.Constraint(
        model.K, rule=route_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            (
                same_loc_cost[kind]
                if origin == dest
                else trip_cost[kind]
            ) * model.trips[kind, origin, dest]
            for kind in model.K
            for origin in model.L
            for dest in model.L
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when no feasible solution can be loaded.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
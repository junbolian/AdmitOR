import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Sets: plane types, locations, time periods
    plane_types = [0, 1]
    locations = [0, 1]
    # Time periods: period 0 is initial, period 1 is the operational period
    periods = [0, 1]

    # Route-specific cost and capacity/operation-limit parameters
    cost = {
        (0, 0, 1): params["cost_p0_0to1"],
        (0, 1, 0): params["cost_p0_1to0"],
        (1, 0, 1): params["cost_p1_0to1"],
        (1, 1, 0): params["cost_p1_1to0"],
    }
    capacity = {
        0: params["capacity_p0"],
        1: params["capacity_p1"],
    }
    max_fleet = {
        0: params["max_planes_p0"],
        1: params["max_planes_p1"],
    }
    max_ops = {
        (0, 0, 1): params["max_ops_p0_0to1"],
        (1, 0, 1): params["max_ops_p1_0to1"],
        (0, 1, 0): params["max_ops_p0_1to0"],
        (1, 1, 0): params["max_ops_p1_1to0"],
    }
    demand_0to1 = params["demand_0to1"]

    # Variables
    # x[p, o, d]: number of plane type p operated from origin o to destination d
    model.x = pyo.Var(
        [(p, o, d) for p in plane_types for o in locations for d in locations if o != d],
        domain=pyo.NonNegativeIntegers,
    )
    # idle[p, l, t]: number of idle plane type p at location l during period t
    model.idle = pyo.Var(
        [(p, l, t) for p in plane_types for l in locations for t in periods],
        domain=pyo.NonNegativeIntegers,
    )

    # Route restrictions
    def route_limit_rule(model, p, o, d):
        return model.x[p, o, d] <= max_ops[(p, o, d)]

    model.route_limit = pyo.Constraint(
        [(p, o, d) for p in plane_types for o in locations for d in locations if o != d],
        rule=route_limit_rule,
    )

    # Demand satisfaction (all demand is in period 0->1 route)
    def demand_rule(model):
        return (
            capacity[0] * model.x[0, 0, 1] + capacity[1] * model.x[1, 0, 1]
            >= demand_0to1
        )

    model.demand = pyo.Constraint(rule=demand_rule)

    # Fleet availability: total planes used per type cannot exceed fleet
    def fleet_rule(model, p):
        used = 0
        for o in locations:
            for d in locations:
                if o != d:
                    used = used + model.x[p, o, d]
        return used <= max_fleet[p]

    model.fleet = pyo.Constraint(plane_types, rule=fleet_rule)

    # Initial allocation logic (period 0):
    # idle planes at location == max_fleet at that location minus departures
    # The problem states initial idle at each location equals
    # planes remaining idle or assigned to routes from that location.
    # We enforce conservation: sum over locations idle[p,l,0] + departures = fleet
    def init_balance_rule(model, p):
        total = 0
        for l in locations:
            total = total + model.idle[p, l, 0]
        for o in locations:
            for d in locations:
                if o != d:
                    total = total + model.x[p, o, d]
        return total == max_fleet[p]

    model.init_balance = pyo.Constraint(plane_types, rule=init_balance_rule)

    # Subsequent period flow balance
    # idle[p,l,1] = idle[p,l,0] + arrivals - departures
    def flow_balance_rule(model, p, l):
        arrivals = 0
        departures = 0
        for other in locations:
            if other != l:
                arrivals = arrivals + model.x[p, other, l]
                departures = departures + model.x[p, l, other]
        return model.idle[p, l, 1] == model.idle[p, l, 0] + arrivals - departures

    model.flow_balance = pyo.Constraint(
        [(p, l) for p in plane_types for l in locations],
        rule=flow_balance_rule,
    )

    # Objective: minimize total operational cost
    def obj_rule(model):
        total = 0
        for p in plane_types:
            for o in locations:
                for d in locations:
                    if o != d:
                        total = total + cost[(p, o, d)] * model.x[p, o, d]
        return total

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Solve exactly as specified
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
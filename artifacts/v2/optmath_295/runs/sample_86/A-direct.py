import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Structural index sets
    model.PLANES = pyo.Set(initialize=[0, 1])
    model.LOCS = pyo.Set(initialize=[0, 1])

    # Ordered route pairs (only the directions that exist)
    route_pairs = [(0, 0, 1), (0, 1, 0), (1, 0, 1), (1, 1, 0)]
    model.ROUTES = pyo.Set(initialize=route_pairs, dimen=3)

    # Parameters
    model.cost = pyo.Param(
        model.ROUTES,
        initialize={
            (0, 0, 1): params["cost_P0_L0_to_L1"],
            (0, 1, 0): params["cost_P0_L1_to_L0"],
            (1, 0, 1): params["cost_P1_L0_to_L1"],
            (1, 1, 0): params["cost_P1_L1_to_L0"],
        },
    )
    model.cost_idle = pyo.Param(initialize=params["cost_idle"])
    model.max_planes = pyo.Param(
        model.PLANES,
        initialize={
            0: params["max_planes_P0"],
            1: params["max_planes_P1"],
        },
    )
    model.demand = pyo.Param(initialize=params["demand_L0_to_L1_period1"])
    model.capacity = pyo.Param(
        model.PLANES,
        initialize={
            0: params["capacity_P0"],
            1: params["capacity_P1"],
        },
    )
    model.max_route = pyo.Param(
        model.ROUTES,
        initialize={
            (0, 0, 1): params["max_route_P0_L0_to_L1"],
            (1, 0, 1): params["max_route_P1_L0_to_L1"],
            (0, 1, 0): params["max_route_P0_L1_to_L0"],
            (1, 1, 0): params["max_route_P1_L1_to_L0"],
        },
    )

    # Decision variables
    model.fly = pyo.Var(model.ROUTES, domain=pyo.NonNegativeIntegers)
    model.idle = pyo.Var(model.PLANES, model.LOCS, domain=pyo.NonNegativeIntegers)

    # Route limits
    def route_limit_rule(m, p, i, j):
        return m.fly[p, i, j] <= m.max_route[p, i, j]
    model.route_limit = pyo.Constraint(model.ROUTES, rule=route_limit_rule)

    # Fleet availability: idle at a location plus departures from it <= fleet size
    def fleet_rule(m, p, i):
        departures = sum(
            m.fly[p, i, j] for (pp, i2, j) in route_pairs if pp == p and i2 == i
        )
        return m.idle[p, i] + departures <= m.max_planes[p]
    model.fleet = pyo.Constraint(model.PLANES, model.LOCS, rule=fleet_rule)

    # Total fleet availability
    def total_fleet_rule(m, p):
        total_idle = sum(m.idle[p, i] for i in m.LOCS)
        total_fly = sum(m.fly[p, i, j] for (pp, i, j) in route_pairs if pp == p)
        return total_idle + total_fly <= m.max_planes[p]
    model.total_fleet = pyo.Constraint(model.PLANES, rule=total_fleet_rule)

    # Demand satisfaction
    def demand_rule(m):
        return sum(m.fly[p, 0, 1] * m.capacity[p] for p in m.PLANES) >= m.demand
    model.demand_con = pyo.Constraint(rule=demand_rule)

    # Objective
    def obj_rule(m):
        operating = sum(m.cost[p, i, j] * m.fly[p, i, j] for (p, i, j) in route_pairs)
        idle_cost = sum(m.cost_idle * m.idle[p, i] for p in m.PLANES for i in m.LOCS)
        return operating + idle_cost
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
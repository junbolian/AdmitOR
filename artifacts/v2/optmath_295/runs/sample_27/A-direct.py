import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    capacities = [params["plane0_capacity"], params["plane1_capacity"]]
    trip_costs = [params["plane0_trip_cost"], params["plane1_trip_cost"]]
    same_loc_costs = [params["plane0_same_loc_cost"], params["plane1_same_loc_cost"]]
    initial_idle = [params["initial_idle_plane0"], params["initial_idle_plane1"]]
    max_idle = [params["max_idle_plane0"], params["max_idle_plane1"]]
    demand = params["demand_1_to_0"]
    max_trips_1to0 = [params["max_trips_plane0_1to0"], params["max_trips_plane1_1to0"]]

    P = [0, 1]
    L = [0, 1]

    model = pyo.ConcreteModel()

    # Trip variables: x[p, i, j] = number of trips by plane type p from i to j
    model.x = pyo.Var(P, L, L, domain=pyo.NonNegativeIntegers)

    # Idle planes at start at each location
    model.idle_start = pyo.Var(P, L, domain=pyo.NonNegativeIntegers)
    model.idle_end = pyo.Var(P, L, domain=pyo.NonNegativeIntegers)

    # Total idle per type must not exceed initial total
    def c_total_idle(m, p):
        return sum(m.idle_start[p, l] for l in L) <= initial_idle[p]
    model.total_idle_con = pyo.Constraint(P, rule=c_total_idle)

    def c_end_idle(m, p):
        return sum(m.idle_end[p, l] for l in L) <= max_idle[p]
    model.end_idle_con = pyo.Constraint(P, rule=c_end_idle)

    # Flow balance: idle_end[p,l] = idle_start[p,l] + arrivals - departures
    def c_balance(m, p, l):
        arrivals = sum(m.x[p, k, l] for k in L if k != l)
        departures = sum(m.x[p, l, k] for k in L if k != l)
        return m.idle_end[p, l] == m.idle_start[p, l] + arrivals - departures
    model.balance_con = pyo.Constraint(P, L, rule=c_balance)

    # Route restrictions: no trips from 0 to 1
    def c_no_0to1(m, p):
        return m.x[p, 0, 1] == 0
    model.no_0to1_con = pyo.Constraint(P, rule=c_no_0to1)

    # Max trips from 1 to 0
    def c_max_1to0(m, p):
        return m.x[p, 1, 0] <= max_trips_1to0[p]
    model.max_1to0_con = pyo.Constraint(P, rule=c_max_1to0)

    # Demand satisfaction
    def c_demand(m):
        return sum(capacities[p] * m.x[p, 1, 0] for p in P) >= demand
    model.demand_con = pyo.Constraint(rule=c_demand)

    # Objective: total operational cost
    def obj_rule(m):
        return sum(
            trip_costs[p] * m.x[p, i, j]
            + (same_loc_costs[p] if i == j else 0) * m.x[p, i, j]
            for p in P for i in L for j in L
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
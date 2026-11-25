# IR: {"sets":{"cities":[0,1,2,3],"nondepot":[1,2,3],"arcs":"(i,j) in cities^2 with i != j"},"params":["travel_cost_0_1","travel_cost_0_2","travel_cost_0_3","travel_cost_1_0","travel_cost_1_2","travel_cost_1_3","travel_cost_2_0","travel_cost_2_1","travel_cost_2_3","travel_cost_3_0","travel_cost_3_1","travel_cost_3_2","u_bound_lower","u_bound_upper","u_depot_fixed"],"variables":{"x[i,j]":"binary for each arc","u[i]":"continuous; nondepot bounds [u_bound_lower,u_bound_upper]; u[0] fixed to u_depot_fixed"},"constraints":["For each i in cities: sum(x[i,j] for j != i) = 1","For each j in cities: sum(x[i,j] for i != j) = 1","For distinct i,j in nondepot: u[i] - u[j] + 4*x[i,j] <= 3"],"objective":"minimize sum(travel_cost_i_j*x[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (0, 1, 2, 3)
    nondepot = (1, 2, 3)
    arcs = tuple((i, j) for i in cities for j in cities if i != j)

    travel_costs = {
        (0, 1): params["travel_cost_0_1"],
        (0, 2): params["travel_cost_0_2"],
        (0, 3): params["travel_cost_0_3"],
        (1, 0): params["travel_cost_1_0"],
        (1, 2): params["travel_cost_1_2"],
        (1, 3): params["travel_cost_1_3"],
        (2, 0): params["travel_cost_2_0"],
        (2, 1): params["travel_cost_2_1"],
        (2, 3): params["travel_cost_2_3"],
        (3, 0): params["travel_cost_3_0"],
        (3, 1): params["travel_cost_3_1"],
        (3, 2): params["travel_cost_3_2"],
    }
    u_lower = params["u_bound_lower"]
    u_upper = params["u_bound_upper"]
    u_depot = params["u_depot_fixed"]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.nondepot = pyo.Set(initialize=nondepot, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(model.arcs, initialize=travel_costs)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds(problem, city):
        if city == 0:
            return (None, None)
        return (u_lower, u_upper)

    model.u = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=position_bounds,
    )
    model.u[0].fix(u_depot)

    def departure_rule(problem, city):
        return sum(
            problem.x[city, destination]
            for destination in problem.cities
            if destination != city
        ) == 1

    model.departure = pyo.Constraint(model.cities, rule=departure_rule)

    def arrival_rule(problem, city):
        return sum(
            problem.x[origin, city]
            for origin in problem.cities
            if origin != city
        ) == 1

    model.arrival = pyo.Constraint(model.cities, rule=arrival_rule)

    def sequencing_rule(problem, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            problem.u[origin]
            - problem.u[destination]
            + 4 * problem.x[origin, destination]
            <= 3
        )

    model.sequencing = pyo.Constraint(
        model.nondepot,
        model.nondepot,
        rule=sequencing_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
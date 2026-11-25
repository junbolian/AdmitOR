# IR: {"sets":{"cities":[0,1,2,3],"nondepot":[1,2,3],"arcs":"(i,j) with i != j","sequencing_pairs":"(i,j) in nondepot x nondepot with i != j"},"params":["travel_cost_0_1","travel_cost_0_2","travel_cost_0_3","travel_cost_1_0","travel_cost_1_2","travel_cost_1_3","travel_cost_2_0","travel_cost_2_1","travel_cost_2_3","travel_cost_3_0","travel_cost_3_1","travel_cost_3_2","u_bound_lower","u_bound_upper","u_depot_fixed"],"derived":{"big_m":"max(4,u_bound_upper-u_bound_lower+1)"},"variables":{"x[i,j]":"binary for all arcs","u[i]":"real; nondepot bounds [u_bound_lower,u_bound_upper]"},"constraints":["sum_j x[i,j] = 1 for each city i","sum_i x[i,j] = 1 for each city j","u[0] = u_depot_fixed","u[i]-u[j]+big_m*x[i,j] <= big_m-1 for each sequencing pair"],"objective":"minimize sum_(i,j) travel_cost_i_j*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (0, 1, 2, 3)
    nondepot = (1, 2, 3)
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    sequencing_pairs = tuple(
        (origin, destination)
        for origin in nondepot
        for destination in nondepot
        if origin != destination
    )

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

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.nondepot = pyo.Set(initialize=nondepot, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.sequencing_pairs = pyo.Set(
        dimen=2, initialize=sequencing_pairs, ordered=True
    )

    model.travel_cost = pyo.Param(
        model.arcs, initialize=travel_costs, within=pyo.Reals
    )
    model.u_lower = pyo.Param(
        initialize=params["u_bound_lower"], within=pyo.Reals
    )
    model.u_upper = pyo.Param(
        initialize=params["u_bound_upper"], within=pyo.Reals
    )
    model.depot_position = pyo.Param(
        initialize=params["u_depot_fixed"], within=pyo.Reals
    )
    model.big_m = pyo.Param(
        initialize=max(
            4,
            pyo.value(model.u_upper) - pyo.value(model.u_lower) + 1,
        ),
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds(instance, city):
        if city == 0:
            return (None, None)
        return (instance.u_lower, instance.u_upper)

    model.u = pyo.Var(
        model.cities, domain=pyo.Reals, bounds=position_bounds
    )
    model.u[0].fix(pyo.value(model.depot_position))

    def departure_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    def sequencing_rule(instance, origin, destination):
        return (
            instance.u[origin]
            - instance.u[destination]
            + instance.big_m * instance.x[origin, destination]
            <= instance.big_m - 1
        )

    model.sequencing_constraints = pyo.Constraint(
        model.sequencing_pairs, rule=sequencing_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"N":[0,1,2,3,4,5,6,7],"C":[1,2,3,4,5,6,7],"A":"{(i,j) in N x N: i != j}","B":"{(i,j) in C x C: i != j}"},"params":{"dist_i_to_j":"params['dist_{i}_to_{j}'] for 0 <= i < j <= 7; symmetric transit times","tw_lower_i":"params['tw{i}_lower'] for i in N","tw_upper_i":"params['tw{i}_upper'] for i in N","s":"params['service_time']","L":"params['max_shelf_life']","M_ij":"max(0, tw_upper_i + s + dist_ij - tw_lower_j)"},"variables":{"x_ij":"binary for (i,j) in A","t_i":"real in [tw_lower_i,tw_upper_i] for i in C","d":"real in [tw_lower_0,tw_upper_0], warehouse departure-stage time before warehouse service","r":"real in [tw_lower_0,tw_upper_0], warehouse return time","u_i":"real in [1,7] for i in C"},"constraints":["sum(j != i, x_ij) = 1 for i in N","sum(i != j, x_ij) = 1 for j in N","u_i - u_j + 7*x_ij <= 6 for (i,j) in B","t_j >= d + s + dist_0j - M_0j*(1-x_0j) for j in C","t_j >= t_i + s + dist_ij - M_ij*(1-x_ij) for (i,j) in B","r >= t_i + s + dist_i0 - M_i0*(1-x_i0) for i in C","0 <= r-d <= L"],"objective":"minimize sum((i,j) in A, dist_ij*x_ij)","conventions":"Time windows include their endpoints; waiting is allowed; warehouse service occurs once before outbound transit; store service occurs after arrival."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    stores = tuple(range(1, 8))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )
    store_arcs = tuple(
        (origin, destination)
        for origin in stores
        for destination in stores
        if origin != destination
    )

    undirected_distances = {
        (origin, destination): float(
            params[f"dist_{origin}_to_{destination}"]
        )
        for origin in nodes
        for destination in nodes
        if origin < destination
    }
    distances = {
        (origin, destination): undirected_distances[
            (min(origin, destination), max(origin, destination))
        ]
        for origin, destination in arcs
    }
    lower = {
        location: float(params[f"tw{location}_lower"])
        for location in nodes
    }
    upper = {
        location: float(params[f"tw{location}_upper"])
        for location in nodes
    }
    service_time = float(params["service_time"])
    shelf_life = float(params["max_shelf_life"])

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.C = pyo.Set(initialize=stores, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.B = pyo.Set(dimen=2, initialize=store_arcs, ordered=True)

    model.transit = pyo.Param(
        model.A, initialize=distances, within=pyo.NonNegativeReals
    )
    model.window_lower = pyo.Param(
        model.N, initialize=lower, within=pyo.Reals
    )
    model.window_upper = pyo.Param(
        model.N, initialize=upper, within=pyo.Reals
    )
    model.service_duration = pyo.Param(
        initialize=service_time, within=pyo.NonNegativeReals
    )
    model.shelf_limit = pyo.Param(
        initialize=shelf_life, within=pyo.NonNegativeReals
    )
    model.big_m = pyo.Param(
        model.A,
        initialize={
            (origin, destination): max(
                0.0,
                upper[origin]
                + service_time
                + distances[origin, destination]
                - lower[destination],
            )
            for origin, destination in arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.route_arc = pyo.Var(model.A, domain=pyo.Binary)
    model.arrival_time = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=lambda mdl, location: (
            mdl.window_lower[location],
            mdl.window_upper[location],
        ),
    )
    model.departure_time = pyo.Var(
        domain=pyo.Reals,
        bounds=(model.window_lower[0], model.window_upper[0]),
    )
    model.return_time = pyo.Var(
        domain=pyo.Reals,
        bounds=(model.window_lower[0], model.window_upper[0]),
    )
    model.visit_order = pyo.Var(
        model.C, domain=pyo.Reals, bounds=(1, len(stores))
    )

    def outgoing_rule(mdl, origin):
        return sum(
            mdl.route_arc[origin, destination]
            for destination in mdl.N
            if destination != origin
        ) == 1

    model.one_outgoing = pyo.Constraint(model.N, rule=outgoing_rule)

    def incoming_rule(mdl, destination):
        return sum(
            mdl.route_arc[origin, destination]
            for origin in mdl.N
            if origin != destination
        ) == 1

    model.one_incoming = pyo.Constraint(model.N, rule=incoming_rule)

    def subtour_rule(mdl, origin, destination):
        return (
            mdl.visit_order[origin]
            - mdl.visit_order[destination]
            + len(stores) * mdl.route_arc[origin, destination]
            <= len(stores) - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.B, rule=subtour_rule
    )

    def departure_timing_rule(mdl, destination):
        return mdl.arrival_time[destination] >= (
            mdl.departure_time
            + mdl.service_duration
            + mdl.transit[0, destination]
            - mdl.big_m[0, destination]
            * (1 - mdl.route_arc[0, destination])
        )

    model.departure_timing = pyo.Constraint(
        model.C, rule=departure_timing_rule
    )

    def store_timing_rule(mdl, origin, destination):
        return mdl.arrival_time[destination] >= (
            mdl.arrival_time[origin]
            + mdl.service_duration
            + mdl.transit[origin, destination]
            - mdl.big_m[origin, destination]
            * (1 - mdl.route_arc[origin, destination])
        )

    model.store_timing = pyo.Constraint(
        model.B, rule=store_timing_rule
    )

    def return_timing_rule(mdl, origin):
        return mdl.return_time >= (
            mdl.arrival_time[origin]
            + mdl.service_duration
            + mdl.transit[origin, 0]
            - mdl.big_m[origin, 0]
            * (1 - mdl.route_arc[origin, 0])
        )

    model.return_timing = pyo.Constraint(
        model.C, rule=return_timing_rule
    )

    model.route_duration = pyo.Constraint(
        expr=pyo.inequality(
            0,
            model.return_time - model.departure_time,
            model.shelf_limit,
        )
    )

    model.total_transit = pyo.Objective(
        expr=sum(
            model.transit[origin, destination]
            * model.route_arc[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Other, unexpected runtime errors must propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_transit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
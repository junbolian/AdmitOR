# IR: {"sets":{"N":"0..7","C":"1..7","A":"{(i,j) in N x N: i != j}","B":"{(i,j) in C x C: i != j}"},"params":{"travel_time":"params['travel_time'], full 8x8 matrix","earliest":"params['tw_0_earliest'] through params['tw_7_earliest']","latest":"params['tw_0_latest'] through params['tw_7_latest']","service_time":"params['service_time']","shelf_life":"params['max_shelf_life_window']"},"variables":{"x[A]":"binary arc selection","t[C]":"real service-start times, bounded by store windows","departure":"real, bounded by depot window","return_time":"real, bounded by depot window","order[C]":"real in [1,7]","margin":"nonnegative common strict-window slack"},"constraints":["Exactly one outgoing arc at every node.","Exactly one incoming arc at every node.","order[i]-order[j]+7*x[i,j] <= 6 for (i,j) in B.","t[j] >= departure+service_time+travel_time[0,j]-M_start[j]*(1-x[0,j]).","t[j] >= t[i]+service_time+travel_time[i,j]-M_between[i,j]*(1-x[i,j]) for (i,j) in B.","return_time >= t[i]+service_time+travel_time[i,0]-M_return[i]*(1-x[i,0]).","return_time-departure <= shelf_life.","earliest[i]+margin <= t[i] <= latest[i]-margin for i in C.","Exclude each candidate route proved unable to achieve positive margin."],"objective":"Minimize sum(travel_time[i,j]*x[i,j] for (i,j) in A).","strict_window_algorithm":"Minimize travel with margin fixed to zero; fix the selected route and maximize margin; return its travel objective if margin is positive, otherwise exclude that route and repeat."}

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
    store_count = len(stores)

    travel_input = params["travel_time"]
    travel = {
        (origin, destination): float(travel_input[origin][destination])
        for origin in nodes
        for destination in nodes
    }
    earliest = {
        node: float(params[f"tw_{node}_earliest"])
        for node in nodes
    }
    latest = {
        node: float(params[f"tw_{node}_latest"])
        for node in nodes
    }
    service = float(params["service_time"])
    shelf_life = float(params["max_shelf_life_window"])

    if service < 0 or shelf_life < 0:
        return {"objective": None, "status": "invalid_parameters"}

    if any(duration < 0 for duration in travel.values()):
        return {"objective": None, "status": "invalid_parameters"}

    if any(earliest[node] > latest[node] for node in nodes):
        return {"objective": None, "status": "infeasible"}

    # Store windows are interpreted literally as open intervals.
    # Depot departure and return bounds remain inclusive.
    if any(earliest[node] >= latest[node] for node in stores):
        return {"objective": None, "status": "infeasible"}

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.C = pyo.Set(initialize=stores, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.B = pyo.Set(dimen=2, initialize=store_arcs, ordered=True)

    model.transit = pyo.Param(
        model.N,
        model.N,
        initialize=travel,
        within=pyo.NonNegativeReals,
    )
    model.window_lower = pyo.Param(model.N, initialize=earliest)
    model.window_upper = pyo.Param(model.N, initialize=latest)
    model.service_duration = pyo.Param(initialize=service)
    model.route_duration_limit = pyo.Param(initialize=shelf_life)

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.t = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=lambda mdl, node: (earliest[node], latest[node]),
    )
    model.departure = pyo.Var(
        domain=pyo.Reals,
        bounds=(earliest[0], latest[0]),
    )
    model.return_time = pyo.Var(
        domain=pyo.Reals,
        bounds=(earliest[0], latest[0]),
    )
    model.order = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, store_count),
    )
    model.margin = pyo.Var(domain=pyo.NonNegativeReals)
    model.margin.fix(0)

    model.outgoing_arcs = pyo.Constraint(
        model.N,
        rule=lambda mdl, origin: sum(
            mdl.x[origin, destination]
            for destination in nodes
            if destination != origin
        ) == 1,
    )

    model.incoming_arcs = pyo.Constraint(
        model.N,
        rule=lambda mdl, destination: sum(
            mdl.x[origin, destination]
            for origin in nodes
            if origin != destination
        ) == 1,
    )

    # Explicit subtour elimination also handles zero travel/service times.
    model.subtour_elimination = pyo.Constraint(
        model.B,
        rule=lambda mdl, origin, destination: (
            mdl.order[origin]
            - mdl.order[destination]
            + store_count * mdl.x[origin, destination]
            <= store_count - 1
        ),
    )

    # Each big-M is derived from the relevant variable bounds.
    start_big_m = {
        destination: max(
            0.0,
            latest[0] + service + travel[0, destination]
            - earliest[destination],
        )
        for destination in stores
    }
    between_big_m = {
        (origin, destination): max(
            0.0,
            latest[origin] + service + travel[origin, destination]
            - earliest[destination],
        )
        for origin, destination in store_arcs
    }
    return_big_m = {
        origin: max(
            0.0,
            latest[origin] + service + travel[origin, 0] - earliest[0],
        )
        for origin in stores
    }

    model.start_timing = pyo.Constraint(
        model.C,
        rule=lambda mdl, destination: (
            mdl.t[destination]
            >= mdl.departure
            + mdl.service_duration
            + mdl.transit[0, destination]
            - start_big_m[destination] * (1 - mdl.x[0, destination])
        ),
    )

    model.between_timing = pyo.Constraint(
        model.B,
        rule=lambda mdl, origin, destination: (
            mdl.t[destination]
            >= mdl.t[origin]
            + mdl.service_duration
            + mdl.transit[origin, destination]
            - between_big_m[origin, destination]
            * (1 - mdl.x[origin, destination])
        ),
    )

    model.return_timing = pyo.Constraint(
        model.C,
        rule=lambda mdl, origin: (
            mdl.return_time
            >= mdl.t[origin]
            + mdl.service_duration
            + mdl.transit[origin, 0]
            - return_big_m[origin] * (1 - mdl.x[origin, 0])
        ),
    )

    model.shelf_life_limit = pyo.Constraint(
        expr=(
            model.return_time - model.departure
            <= model.route_duration_limit
        )
    )

    model.strict_lower_windows = pyo.Constraint(
        model.C,
        rule=lambda mdl, node: (
            mdl.t[node] >= mdl.window_lower[node] + mdl.margin
        ),
    )
    model.strict_upper_windows = pyo.Constraint(
        model.C,
        rule=lambda mdl, node: (
            mdl.t[node] <= mdl.window_upper[node] - mdl.margin
        ),
    )

    model.excluded_routes = pyo.ConstraintList()

    model.total_travel = pyo.Objective(
        expr=sum(
            model.transit[origin, destination]
            * model.x[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )
    model.window_margin_objective = pyo.Objective(
        expr=model.margin,
        sense=pyo.maximize,
    )
    model.window_margin_objective.deactivate()

    # Strict inequalities cannot be imposed directly in an MILP. Instead,
    # test whether each candidate route admits a positive common margin.
    # There are finitely many tours, so excluding failed candidates terminates.
    while True:
        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solve_failed"}

        try:
            obj_val = float(pyo.value(model.total_travel))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        selected_arcs = tuple(
            (origin, destination)
            for origin, destination in arcs
            if pyo.value(model.x[origin, destination]) > 0.5
        )
        selected_set = set(selected_arcs)

        for origin, destination in arcs:
            model.x[origin, destination].fix(
                int((origin, destination) in selected_set)
            )

        model.margin.unfix()
        model.total_travel.deactivate()
        model.window_margin_objective.activate()

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solve_failed"}

        try:
            margin_val = float(
                pyo.value(model.window_margin_objective)
            )
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if margin_val > 0:
            try:
                obj_val = float(pyo.value(model.total_travel))
            except (ValueError, TypeError):
                return {
                    "objective": None,
                    "status": "objective_unavailable",
                }
            return {"objective": obj_val, "status": "optimal"}

        for origin, destination in arcs:
            model.x[origin, destination].unfix()

        model.excluded_routes.add(
            sum(
                model.x[origin, destination]
                for origin, destination in selected_arcs
            ) <= len(selected_arcs) - 1
        )

        model.window_margin_objective.deactivate()
        model.total_travel.activate()
        model.margin.fix(0)
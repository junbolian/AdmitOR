# IR: {"sets":{"N":"0..num_nodes-1","H":"1..num_hospitals","A":"{(i,j) in N x N: i != j}"},"params":{"num_nodes":"params['num_nodes']; frozen at 8","num_hospitals":"params['num_hospitals']; frozen at 7","travel_time_i":"params['travel_time_i'][j] for i,j in N","window_i_start":"params['window_i_start'] for i in N","window_i_end":"params['window_i_end'] for i in N","horizon":"params['horizon']","service_time":"params['service_time']","M_ij":"horizon + service_time + travel_time_i[j]"},"variables":{"x[i,j]":"binary for (i,j) in A","arrival[i]":"continuous in [0,horizon] for i in N; arrival[0] is initial hub service time","return_time":"continuous in [0,horizon]; final hub arrival time","visit_order[i]":"continuous in [1,num_hospitals] for i in H"},"constraints":["sum(j != i) x[i,j] = 1 for i in N","sum(i != j) x[i,j] = 1 for j in N","window_i_start <= arrival[i] <= window_i_end for i in N","window_0_start <= return_time <= window_0_end","arrival[j] >= arrival[i] + service_time + travel_time_i[j] - M_ij*(1-x[i,j]) for (i,j) in A with j in H","return_time >= arrival[i] + service_time + travel_time_i[0] - M_i0*(1-x[i,0]) for i in H","visit_order[i] - visit_order[j] + num_hospitals*x[i,j] <= num_hospitals-1 for distinct i,j in H"],"objective":"minimize sum((i,j) in A) travel_time_i[j]*x[i,j]","conventions":"Reception intervals are closed as specified by [start,end]; waiting is allowed; route completion is final hub arrival."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    num_hospitals = int(params["num_hospitals"])

    if num_nodes != 8 or num_hospitals != 7:
        raise ValueError("The frozen network requires 8 nodes and 7 hospitals.")

    nodes = range(num_nodes)
    hospitals = range(1, num_hospitals + 1)

    travel_rows = {
        node: params[f"travel_time_{node}"]
        for node in nodes
    }
    travel_times = {
        (origin, destination): float(travel_rows[origin][destination])
        for origin in nodes
        for destination in nodes
    }
    window_starts = {
        node: float(params[f"window_{node}_start"])
        for node in nodes
    }
    window_ends = {
        node: float(params[f"window_{node}_end"])
        for node in nodes
    }
    horizon = float(params["horizon"])
    service_time = float(params["service_time"])

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.hospitals = pyo.Set(initialize=hospitals, ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in nodes
            for destination in nodes
            if origin != destination
        ],
    )
    model.hospital_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in hospitals
            for destination in hospitals
            if origin != destination
        ],
    )

    model.travel_time = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=travel_times,
        within=pyo.NonNegativeReals,
    )
    model.window_start = pyo.Param(
        model.nodes,
        initialize=window_starts,
        within=pyo.Reals,
    )
    model.window_end = pyo.Param(
        model.nodes,
        initialize=window_ends,
        within=pyo.Reals,
    )
    model.route_horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )
    model.service_duration = pyo.Param(
        initialize=service_time,
        within=pyo.NonNegativeReals,
    )
    model.big_m = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): (
                horizon + service_time + travel_times[origin, destination]
            )
            for origin in nodes
            for destination in nodes
            if origin != destination
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.arrival = pyo.Var(
        model.nodes,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.return_time = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.visit_order = pyo.Var(
        model.hospitals,
        domain=pyo.Reals,
        bounds=(1, num_hospitals),
    )

    def outgoing_rule(mod, origin):
        return sum(
            mod.x[origin, destination]
            for destination in mod.nodes
            if destination != origin
        ) == 1

    model.one_departure = pyo.Constraint(
        model.nodes, rule=outgoing_rule
    )

    def incoming_rule(mod, destination):
        return sum(
            mod.x[origin, destination]
            for origin in mod.nodes
            if origin != destination
        ) == 1

    model.one_arrival = pyo.Constraint(
        model.nodes, rule=incoming_rule
    )

    def reception_window_rule(mod, node):
        return (
            mod.window_start[node],
            mod.arrival[node],
            mod.window_end[node],
        )

    model.reception_windows = pyo.Constraint(
        model.nodes, rule=reception_window_rule
    )
    model.hub_return_window = pyo.Constraint(
        expr=(
            model.window_start[0],
            model.return_time,
            model.window_end[0],
        )
    )

    def hospital_timing_rule(mod, origin, destination):
        if destination == 0:
            return pyo.Constraint.Skip
        return mod.arrival[destination] >= (
            mod.arrival[origin]
            + mod.service_duration
            + mod.travel_time[origin, destination]
            - mod.big_m[origin, destination]
            * (1 - mod.x[origin, destination])
        )

    model.hospital_timing = pyo.Constraint(
        model.arcs, rule=hospital_timing_rule
    )

    def return_timing_rule(mod, origin):
        return mod.return_time >= (
            mod.arrival[origin]
            + mod.service_duration
            + mod.travel_time[origin, 0]
            - mod.big_m[origin, 0] * (1 - mod.x[origin, 0])
        )

    model.return_timing = pyo.Constraint(
        model.hospitals, rule=return_timing_rule
    )

    def subtour_rule(mod, origin, destination):
        return (
            mod.visit_order[origin]
            - mod.visit_order[destination]
            + num_hospitals * mod.x[origin, destination]
            <= num_hospitals - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.hospital_pairs, rule=subtour_rule
    )

    model.total_travel_time = pyo.Objective(
        expr=sum(
            model.travel_time[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no feasible solution can be loaded.
    # Success is determined exclusively by objective-value retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_travel_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
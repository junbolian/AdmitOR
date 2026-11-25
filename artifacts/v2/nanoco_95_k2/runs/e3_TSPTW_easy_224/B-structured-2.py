# IR: {"sets":{"ATMS":"1..7","NODES":"0..8, with 0=start vault and 8=return vault","ARCS":"(0,j), (i,j) for distinct ATMs, and (i,8)"},"params":["vault_x","vault_y","atm_x","atm_y","travel_time_0_to_atm","travel_time_atm1_to_atm","travel_time_atm2_to_atm","travel_time_atm3_to_atm","travel_time_atm4_to_atm","travel_time_atm5_to_atm","travel_time_atm6_to_atm7","vault_window_start","vault_window_end","atm_window_start","atm_window_end","horizon"],"derived":{"physical_node":"8 maps to 0; other nodes unchanged","distance":"Euclidean distance between supplied coordinates","travel":"symmetric matrix from supplied travel times","L":"max(0, applicable window start)","U":"min(horizon, applicable window end)","M[i,j]":"max(0,U[i]+travel[i,j]-L[j])"},"variables":{"x[i,j]":"binary for ARCS","t[i]":"continuous nonnegative service time for NODES","u[i]":"continuous in [1,7] for ATMS"},"constraints":["Exactly one arc leaves the start vault.","Exactly one arc enters the return vault.","Exactly one arc enters each ATM.","Exactly one arc leaves each ATM.","L[i] <= t[i] <= U[i] for each node.","t[j] >= t[i]+travel[i,j]-M[i,j]*(1-x[i,j]) for each arc; service durations are zero and waiting is allowed.","u[i]-u[j]+7*x[i,j] <= 6 for distinct ATMs, eliminating subtours."],"objective":"Minimize sum(distance[i,j]*x[i,j] for all arcs); supplied travel times govern scheduling."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vault_x = float(params["vault_x"])
    vault_y = float(params["vault_y"])
    atm_x = [float(value) for value in params["atm_x"]]
    atm_y = [float(value) for value in params["atm_y"]]

    travel_rows = {
        0: [float(value) for value in params["travel_time_0_to_atm"]],
        1: [float(value) for value in params["travel_time_atm1_to_atm"]],
        2: [float(value) for value in params["travel_time_atm2_to_atm"]],
        3: [float(value) for value in params["travel_time_atm3_to_atm"]],
        4: [float(value) for value in params["travel_time_atm4_to_atm"]],
        5: [float(value) for value in params["travel_time_atm5_to_atm"]],
        6: [float(params["travel_time_atm6_to_atm7"])],
    }

    vault_window_start = float(params["vault_window_start"])
    vault_window_end = float(params["vault_window_end"])
    atm_window_start = [
        float(value) for value in params["atm_window_start"]
    ]
    atm_window_end = [
        float(value) for value in params["atm_window_end"]
    ]
    horizon = float(params["horizon"])

    atms = tuple(range(1, 8))
    nodes = tuple(range(9))
    return_node = 8

    if any(
        len(values) != len(atms)
        for values in (atm_x, atm_y, atm_window_start, atm_window_end)
    ):
        raise ValueError("ATM coordinate and window arrays must each have length 7.")

    for origin, row in travel_rows.items():
        if len(row) != 7 - origin:
            raise ValueError("Travel-time rows have incorrect lengths.")

    coordinates = {0: (vault_x, vault_y)}
    coordinates.update({
        node: (atm_x[node - 1], atm_y[node - 1])
        for node in atms
    })
    coordinates[return_node] = coordinates[0]

    travel_matrix = {}
    for origin, row in travel_rows.items():
        for destination, value in enumerate(row, start=origin + 1):
            travel_matrix[origin, destination] = value
            travel_matrix[destination, origin] = value

    arcs = (
        [(0, destination) for destination in atms]
        + [
            (origin, destination)
            for origin in atms
            for destination in atms
            if origin != destination
        ]
        + [(origin, return_node) for origin in atms]
    )

    lower = {
        0: max(0.0, vault_window_start),
        return_node: max(0.0, vault_window_start),
    }
    upper = {
        0: min(horizon, vault_window_end),
        return_node: min(horizon, vault_window_end),
    }
    for node in atms:
        lower[node] = max(0.0, atm_window_start[node - 1])
        upper[node] = min(horizon, atm_window_end[node - 1])

    distance = {}
    travel = {}
    big_m = {}
    for origin, destination in arcs:
        origin_x, origin_y = coordinates[origin]
        destination_x, destination_y = coordinates[destination]
        distance[origin, destination] = math.hypot(
            origin_x - destination_x,
            origin_y - destination_y,
        )

        physical_destination = (
            0 if destination == return_node else destination
        )
        travel[origin, destination] = travel_matrix[
            origin, physical_destination
        ]
        big_m[origin, destination] = max(
            0.0,
            upper[origin]
            + travel[origin, destination]
            - lower[destination],
        )

    model = pyo.ConcreteModel()
    model.atms = pyo.Set(initialize=atms, ordered=True)
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.t = pyo.Var(model.nodes, domain=pyo.NonNegativeReals)
    model.u = pyo.Var(
        model.atms,
        domain=pyo.Reals,
        bounds=(1, len(atms)),
    )

    model.start_departure = pyo.Constraint(
        expr=sum(model.x[0, destination] for destination in atms) == 1
    )
    model.vault_return = pyo.Constraint(
        expr=sum(model.x[origin, return_node] for origin in atms) == 1
    )

    def incoming_rule(model, destination):
        return sum(
            model.x[origin, destination]
            for origin in (0,) + atms
            if origin != destination
        ) == 1

    def outgoing_rule(model, origin):
        return sum(
            model.x[origin, destination]
            for destination in atms + (return_node,)
            if destination != origin
        ) == 1

    model.atm_incoming = pyo.Constraint(model.atms, rule=incoming_rule)
    model.atm_outgoing = pyo.Constraint(model.atms, rule=outgoing_rule)

    def window_lower_rule(model, node):
        return model.t[node] >= lower[node]

    def window_upper_rule(model, node):
        return model.t[node] <= upper[node]

    model.window_lower = pyo.Constraint(
        model.nodes, rule=window_lower_rule
    )
    model.window_upper = pyo.Constraint(
        model.nodes, rule=window_upper_rule
    )

    def sequencing_rule(model, origin, destination):
        return model.t[destination] >= (
            model.t[origin]
            + travel[origin, destination]
            - big_m[origin, destination]
            * (1 - model.x[origin, destination])
        )

    model.time_sequencing = pyo.Constraint(
        model.arcs, rule=sequencing_rule
    )

    def subtour_rule(model, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            model.u[origin]
            - model.u[destination]
            + len(atms) * model.x[origin, destination]
            <= len(atms) - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.atms, model.atms, rule=subtour_rule
    )

    model.total_mileage = pyo.Objective(
        expr=sum(
            distance[origin, destination] * model.x[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_mileage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
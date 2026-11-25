# IR: {"sets":{"C":"{1,...,7}","V":"{0,...,8}; 0=start vault, 8=return vault","A":"{(i,j): i in {0,...,7}, j in {1,...,8}, i!=j, (i,j)!=(0,8)}"},"params":{"coordinates":"vault_depot_x, vault_depot_y, atm_x, atm_y","travel_times":"vault_to_atm_times, atm1_to_atm_times, atm2_to_atm_times, atm3_to_atm_times, atm4_to_atm_times, atm5_to_atm_times, atm6_to_atm7_time; symmetric","windows":"vault_time_window_start/end, atm1_time_window_start/end,...,atm7_time_window_start/end","limits":"horizon, service_time","distance":"Euclidean distance from coordinates","L_U":"node windows; return-vault upper bound=min(vault_time_window_end,horizon)","M_ij":"max(0,U_i+service_time+travel_time_ij-L_j)"},"variables":{"x_ij":"binary for (i,j) in A","t_i":"real service-start time in [L_i,U_i] for i in V","u_i":"real in [1,7] for i in C"},"constraints":["Exactly one arc leaves start vault.","Exactly one arc enters return vault.","Exactly one arc enters each ATM.","Exactly one arc leaves each ATM.","u_i-u_j+7*x_ij<=6 for distinct ATMs i,j.","t_j>=t_i+service_time+travel_time_ij-M_ij*(1-x_ij) for every arc.","t_8-t_0<=horizon."],"objective":"minimize sum(distance_ij*x_ij for (i,j) in A)"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the patrol problem using Euclidean mileage and supplied travel times.

    Coordinate and travel-time arrays must follow the ascending ATM order
    specified in the problem. Time windows apply to service-start times.
    """
    customers = tuple(range(1, 8))
    nodes = tuple(range(9))
    start_node = 0
    return_node = 8
    customer_count = len(customers)

    vault_x = float(params["vault_depot_x"])
    vault_y = float(params["vault_depot_y"])
    atm_x = tuple(float(value) for value in params["atm_x"])
    atm_y = tuple(float(value) for value in params["atm_y"])

    travel_rows = {
        0: tuple(float(value) for value in params["vault_to_atm_times"]),
        1: tuple(float(value) for value in params["atm1_to_atm_times"]),
        2: tuple(float(value) for value in params["atm2_to_atm_times"]),
        3: tuple(float(value) for value in params["atm3_to_atm_times"]),
        4: tuple(float(value) for value in params["atm4_to_atm_times"]),
        5: tuple(float(value) for value in params["atm5_to_atm_times"]),
        6: (float(params["atm6_to_atm7_time"]),),
    }

    vault_start = float(params["vault_time_window_start"])
    vault_end = float(params["vault_time_window_end"])
    windows = {
        0: (vault_start, vault_end),
        1: (
            float(params["atm1_time_window_start"]),
            float(params["atm1_time_window_end"]),
        ),
        2: (
            float(params["atm2_time_window_start"]),
            float(params["atm2_time_window_end"]),
        ),
        3: (
            float(params["atm3_time_window_start"]),
            float(params["atm3_time_window_end"]),
        ),
        4: (
            float(params["atm4_time_window_start"]),
            float(params["atm4_time_window_end"]),
        ),
        5: (
            float(params["atm5_time_window_start"]),
            float(params["atm5_time_window_end"]),
        ),
        6: (
            float(params["atm6_time_window_start"]),
            float(params["atm6_time_window_end"]),
        ),
        7: (
            float(params["atm7_time_window_start"]),
            float(params["atm7_time_window_end"]),
        ),
    }
    horizon = float(params["horizon"])
    service_time = float(params["service_time"])
    windows[return_node] = (vault_start, min(vault_end, horizon))

    if len(atm_x) != customer_count or len(atm_y) != customer_count:
        raise ValueError("atm_x and atm_y must each contain seven coordinates.")
    for origin, row_values in travel_rows.items():
        if len(row_values) != customer_count - origin:
            raise ValueError("A travel-time row has an incorrect length.")

    numeric_values = [vault_x, vault_y, horizon, service_time]
    numeric_values.extend(atm_x)
    numeric_values.extend(atm_y)
    for row_values in travel_rows.values():
        numeric_values.extend(row_values)
    for lower, upper in windows.values():
        numeric_values.extend((lower, upper))
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError("All numeric parameters must be finite.")
    if horizon < 0 or service_time < 0:
        raise ValueError("horizon and service_time must be nonnegative.")
    if any(value < 0 for row_values in travel_rows.values()
           for value in row_values):
        raise ValueError("Travel times must be nonnegative.")

    coordinates = {start_node: (vault_x, vault_y)}
    coordinates.update({
        customer: (atm_x[customer - 1], atm_y[customer - 1])
        for customer in customers
    })
    coordinates[return_node] = coordinates[start_node]

    physical_times = {}
    for origin, row_values in travel_rows.items():
        for destination, travel_time in zip(
            range(origin + 1, customer_count + 1), row_values
        ):
            physical_times[origin, destination] = travel_time
            physical_times[destination, origin] = travel_time

    arcs = tuple(
        (origin, destination)
        for origin in (start_node,) + customers
        for destination in customers + (return_node,)
        if origin != destination
        and (origin, destination) != (start_node, return_node)
    )
    travel_times = {
        (origin, destination): physical_times[
            origin, start_node if destination == return_node else destination
        ]
        for origin, destination in arcs
    }
    distances = {
        (origin, destination): math.hypot(
            coordinates[origin][0] - coordinates[destination][0],
            coordinates[origin][1] - coordinates[destination][1],
        )
        for origin, destination in arcs
    }
    big_m = {
        (origin, destination): max(
            0.0,
            windows[origin][1]
            + service_time
            + travel_times[origin, destination]
            - windows[destination][0],
        )
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.customers = pyo.Set(initialize=customers, ordered=True)
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.route_arc = pyo.Var(model.arcs, domain=pyo.Binary)
    model.service_start = pyo.Var(
        model.nodes,
        domain=pyo.Reals,
        bounds=lambda instance, node: windows[node],
    )
    model.visit_order = pyo.Var(
        model.customers,
        domain=pyo.Reals,
        bounds=(1, customer_count),
    )

    model.depart_vault = pyo.Constraint(
        expr=sum(
            model.route_arc[start_node, customer]
            for customer in customers
        ) == 1
    )
    model.return_vault = pyo.Constraint(
        expr=sum(
            model.route_arc[customer, return_node]
            for customer in customers
        ) == 1
    )

    def incoming_rule(instance, customer):
        return sum(
            instance.route_arc[origin, customer]
            for origin in (start_node,) + customers
            if origin != customer
        ) == 1

    def outgoing_rule(instance, customer):
        return sum(
            instance.route_arc[customer, destination]
            for destination in customers + (return_node,)
            if destination != customer
        ) == 1

    model.visit_incoming = pyo.Constraint(
        model.customers, rule=incoming_rule
    )
    model.visit_outgoing = pyo.Constraint(
        model.customers, rule=outgoing_rule
    )

    def subtour_rule(instance, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            instance.visit_order[origin]
            - instance.visit_order[destination]
            + customer_count * instance.route_arc[origin, destination]
            <= customer_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.customers, model.customers, rule=subtour_rule
    )

    def time_rule(instance, origin, destination):
        return (
            instance.service_start[destination]
            >= instance.service_start[origin]
            + service_time
            + travel_times[origin, destination]
            - big_m[origin, destination]
            * (1 - instance.route_arc[origin, destination])
        )

    model.time_propagation = pyo.Constraint(
        model.arcs, rule=time_rule
    )
    model.shift_duration = pyo.Constraint(
        expr=model.service_start[return_node]
        - model.service_start[start_node] <= horizon
    )
    model.total_mileage = pyo.Objective(
        expr=sum(
            distances[origin, destination]
            * model.route_arc[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading finds no solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_mileage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
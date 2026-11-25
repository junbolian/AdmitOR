# IR: {"sets":{"C":"{1,...,7}","V":"{0,...,8}; 0=start vault, 8=return vault","S":"{0,...,7}","D":"{1,...,8}","A":"{(i,j): i in S, j in D, i!=j, (i,j)!=(0,8)}"},"params":{"inputs":["vault_x","vault_y","atm_x","atm_y","travel_time_0_to_atm","travel_time_atm1_to_atm","travel_time_atm2_to_atm","travel_time_atm3_to_atm","travel_time_atm4_to_atm","travel_time_atm5_to_atm","travel_time_atm6_to_atm7","vault_window_start","vault_window_end","atm_window_start","atm_window_end","horizon"],"derived":["coordinates[0]=coordinates[8]=vault coordinates; coordinates[1..7]=ATM coordinates","T=symmetric supplied travel-time matrix; return-vault travel times equal start-vault travel times","d[i,j]=Euclidean coordinate distance","L[i]=max(0,window_start[i]); U[i]=min(horizon,window_end[i]); nodes 0 and 8 use vault windows","M[i,j]=max(0,U[i]+T[i,j]-L[j])"]},"variables":{"x[i,j]":"Binary, (i,j) in A","t[i]":"NonnegativeReal, L[i]<=t[i]<=U[i], i in V","u[i]":"Real, 1<=u[i]<=7, i in C"},"constraints":["sum(x[i,j] for outgoing arcs)=1 for each i in S","sum(x[i,j] for incoming arcs)=1 for each j in D","t[j]>=t[i]+T[i,j]-M[i,j]*(1-x[i,j]) for each (i,j) in A; zero service duration and waiting allowed","u[j]>=u[i]+1-7*(1-x[i,j]) for distinct i,j in C"],"objective":"minimize sum(d[i,j]*x[i,j] for (i,j) in A)"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Coordinates determine mileage; supplied travel times determine feasibility.
    vault_x = float(params["vault_x"])
    vault_y = float(params["vault_y"])
    atm_x = [float(value) for value in params["atm_x"]]
    atm_y = [float(value) for value in params["atm_y"]]

    supplied_travel_rows = [
        [float(value) for value in params["travel_time_0_to_atm"]],
        [float(value) for value in params["travel_time_atm1_to_atm"]],
        [float(value) for value in params["travel_time_atm2_to_atm"]],
        [float(value) for value in params["travel_time_atm3_to_atm"]],
        [float(value) for value in params["travel_time_atm4_to_atm"]],
        [float(value) for value in params["travel_time_atm5_to_atm"]],
        [float(params["travel_time_atm6_to_atm7"])],
    ]

    vault_window_start = float(params["vault_window_start"])
    vault_window_end = float(params["vault_window_end"])
    atm_window_start = [
        float(value) for value in params["atm_window_start"]
    ]
    atm_window_end = [
        float(value) for value in params["atm_window_end"]
    ]
    horizon = float(params["horizon"])

    customer_count = 7
    start_node = 0
    return_node = customer_count + 1

    customers = list(range(1, customer_count + 1))
    nodes = list(range(return_node + 1))
    sources = [start_node] + customers
    destinations = customers + [return_node]

    if any(
        len(sequence) != customer_count
        for sequence in (
            atm_x,
            atm_y,
            atm_window_start,
            atm_window_end,
        )
    ):
        raise ValueError("Coordinate and ATM-window arrays must each have length 7.")

    for origin, row in enumerate(supplied_travel_rows):
        if len(row) != customer_count - origin:
            raise ValueError("A supplied travel-time row has an incorrect length.")

    numeric_values = [
        vault_x,
        vault_y,
        vault_window_start,
        vault_window_end,
        horizon,
    ]
    numeric_values.extend(atm_x)
    numeric_values.extend(atm_y)
    numeric_values.extend(atm_window_start)
    numeric_values.extend(atm_window_end)
    for row in supplied_travel_rows:
        numeric_values.extend(row)

    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError("All numeric inputs must be finite.")

    if any(value < 0 for row in supplied_travel_rows for value in row):
        raise ValueError("Travel times must be nonnegative.")

    coordinates = {
        start_node: (vault_x, vault_y),
        return_node: (vault_x, vault_y),
    }
    for customer in customers:
        coordinates[customer] = (
            atm_x[customer - 1],
            atm_y[customer - 1],
        )

    travel_times = {}
    for origin, row in enumerate(supplied_travel_rows):
        for destination, duration in enumerate(row, start=origin + 1):
            travel_times[origin, destination] = duration
            travel_times[destination, origin] = duration

    for customer in customers:
        travel_times[customer, return_node] = travel_times[
            customer, start_node
        ]

    window_starts = {
        start_node: vault_window_start,
        return_node: vault_window_start,
    }
    window_ends = {
        start_node: vault_window_end,
        return_node: vault_window_end,
    }
    for customer in customers:
        window_starts[customer] = atm_window_start[customer - 1]
        window_ends[customer] = atm_window_end[customer - 1]

    lower_bounds = {
        node: max(0.0, window_starts[node]) for node in nodes
    }
    upper_bounds = {
        node: min(horizon, window_ends[node]) for node in nodes
    }

    if any(lower_bounds[node] > upper_bounds[node] for node in nodes):
        return {"objective": None, "status": "infeasible"}

    arcs = [
        (origin, destination)
        for origin in sources
        for destination in destinations
        if origin != destination
        and (origin, destination) != (start_node, return_node)
    ]

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
            upper_bounds[origin]
            + travel_times[origin, destination]
            - lower_bounds[destination],
        )
        for origin, destination in arcs
    }

    outgoing = {
        origin: [
            destination
            for candidate_origin, destination in arcs
            if candidate_origin == origin
        ]
        for origin in sources
    }
    incoming = {
        destination: [
            origin
            for origin, candidate_destination in arcs
            if candidate_destination == destination
        ]
        for destination in destinations
    }

    model = pyo.ConcreteModel()
    model.customer_nodes = pyo.Set(initialize=customers, ordered=True)
    model.route_nodes = pyo.Set(initialize=nodes, ordered=True)
    model.source_nodes = pyo.Set(initialize=sources, ordered=True)
    model.destination_nodes = pyo.Set(initialize=destinations, ordered=True)
    model.route_arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.customer_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in customers
            for destination in customers
            if origin != destination
        ],
        ordered=True,
    )

    model.arc_used = pyo.Var(model.route_arcs, domain=pyo.Binary)
    model.service_time = pyo.Var(
        model.route_nodes,
        domain=pyo.NonNegativeReals,
        bounds=lambda instance, node: (
            lower_bounds[node],
            upper_bounds[node],
        ),
    )
    model.visit_order = pyo.Var(
        model.customer_nodes,
        domain=pyo.Reals,
        bounds=(1, customer_count),
    )

    def outgoing_rule(instance, origin):
        return sum(
            instance.arc_used[origin, destination]
            for destination in outgoing[origin]
        ) == 1

    model.outgoing_degree = pyo.Constraint(
        model.source_nodes, rule=outgoing_rule
    )

    def incoming_rule(instance, destination):
        return sum(
            instance.arc_used[origin, destination]
            for origin in incoming[destination]
        ) == 1

    model.incoming_degree = pyo.Constraint(
        model.destination_nodes, rule=incoming_rule
    )

    def time_rule(instance, origin, destination):
        return instance.service_time[destination] >= (
            instance.service_time[origin]
            + travel_times[origin, destination]
            - big_m[origin, destination]
            * (1 - instance.arc_used[origin, destination])
        )

    model.time_precedence = pyo.Constraint(
        model.route_arcs, rule=time_rule
    )

    def order_rule(instance, origin, destination):
        return instance.visit_order[destination] >= (
            instance.visit_order[origin]
            + 1
            - customer_count
            * (1 - instance.arc_used[origin, destination])
        )

    model.subtour_elimination = pyo.Constraint(
        model.customer_arcs, rule=order_rule
    )

    model.total_mileage = pyo.Objective(
        expr=sum(
            distances[origin, destination]
            * model.arc_used[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPSI raises this when it cannot load a feasible solution.
        # Unexpected solver errors are allowed to propagate.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_mileage))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
# {
#   "sets": {"V": "input node indices, including depot 0", "C": "V excluding 0", "A": "ordered pairs (i,j) in V x V with i != j", "B": "ordered pairs (i,j) in C x C with i != j"},
#   "params": {"Q": "params['vehicle_capacity']", "q": "params['customer_demand']", "a": "params['earliest_service_time']", "b": "params['latest_service_time']", "s": "params['service_time']", "X": "params['x_coordinate']", "Y": "params['y_coordinate']", "n": "|C|", "d[i,j]": "hypot(X[i]-X[j], Y[i]-Y[j]); travel distance equals travel time", "M[i,j]": "max(0,b[i]+s[i]+d[i,j]-a[j])"},
#   "variables": {"x[i,j]": "binary for (i,j) in A", "t[i]": "real in [a[i],b[i]] for i in C", "u[i]": "real in [q[i],Q] for i in C; cumulative delivered load", "r[i]": "real in [1,n] for i in C; route position", "z": "real with bounds [0,0]; ensures a nonempty solver model"},
#   "constraints": [
#     "sum(j in V excluding i) x[i,j] = 1 for each i in C",
#     "sum(j in V excluding i) x[j,i] = 1 for each i in C",
#     "sum(j in C) x[0,j] - sum(i in C) x[i,0] = z",
#     "u[j] >= u[i] + q[j] - Q*(1-x[i,j]) for each (i,j) in B",
#     "r[j] >= r[i] + 1 - n*(1-x[i,j]) for each (i,j) in B",
#     "t[j] >= t[i] + s[i] + d[i,j] - M[i,j]*(1-x[i,j]) for each (i,j) in B",
#     "t[j] >= a[0] + s[0] + d[0,j] - max(0,a[0]+s[0]+d[0,j]-a[j])*(1-x[0,j]) for each j in C",
#     "t[i] + s[i] + d[i,0] <= b[0] + max(0,b[i]+s[i]+d[i,0]-b[0])*(1-x[i,0]) for each i in C"
#   ],
#   "objective": "minimize sum((i,j) in A) d[i,j]*x[i,j] + z"
# }

from collections.abc import Mapping
from math import hypot, isfinite

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve a homogeneous-fleet VRP with hard service-start time windows.

    Node data may be sequences indexed from zero or mappings with integer
    node IDs (integer-string keys are also accepted). Depot ID is zero.
    Every node-data parameter must contain the same node IDs.

    Euclidean distance supplies both travel cost and travel time. The fleet
    may use up to one vehicle per customer, with no vehicle-use charge.
    Each route starts at the depot and returns by its closing time.
    Customer service must start, but need not finish, within its window.
    """

    def normalize_node_data(values):
        if isinstance(values, Mapping):
            normalized = {}
            for key, value in values.items():
                if isinstance(key, str):
                    try:
                        node = int(key)
                    except ValueError:
                        raise ValueError(
                            "Node mapping keys must be integer IDs."
                        ) from None
                elif isinstance(key, int) and not isinstance(key, bool):
                    node = key
                else:
                    raise ValueError("Node mapping keys must be integer IDs.")
                if node in normalized:
                    raise ValueError("Duplicate normalized node ID.")
                normalized[node] = float(value)
            return normalized

        return {node: float(value) for node, value in enumerate(values)}

    capacity = float(params["vehicle_capacity"])
    demand = normalize_node_data(params["customer_demand"])
    earliest = normalize_node_data(params["earliest_service_time"])
    latest = normalize_node_data(params["latest_service_time"])
    duration = normalize_node_data(params["service_time"])
    horizontal = normalize_node_data(params["x_coordinate"])
    vertical = normalize_node_data(params["y_coordinate"])

    node_ids = set(demand)
    if 0 not in node_ids:
        return {"objective": None, "status": "invalid_depot"}

    node_parameters = (
        demand,
        earliest,
        latest,
        duration,
        horizontal,
        vertical,
    )
    if any(set(values) != node_ids for values in node_parameters):
        return {"objective": None, "status": "inconsistent_node_data"}

    if not isfinite(capacity) or capacity < 0:
        return {"objective": None, "status": "invalid_capacity"}

    if any(
        not isfinite(value)
        for values in node_parameters
        for value in values.values()
    ):
        return {"objective": None, "status": "invalid_numeric_data"}

    if demand[0] != 0:
        return {"objective": None, "status": "invalid_depot_demand"}

    if any(demand[node] < 0 or duration[node] < 0 for node in node_ids):
        return {"objective": None, "status": "invalid_negative_data"}

    if any(earliest[node] > latest[node] for node in node_ids):
        return {"objective": None, "status": "infeasible"}

    nodes = sorted(node_ids)
    customers = [node for node in nodes if node != 0]
    customer_count = len(customers)

    if any(demand[node] > capacity for node in customers):
        return {"objective": None, "status": "infeasible"}

    arcs = [
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    ]
    customer_arcs = [
        (origin, destination)
        for origin in customers
        for destination in customers
        if origin != destination
    ]

    distance = {
        (origin, destination): hypot(
            horizontal[origin] - horizontal[destination],
            vertical[origin] - vertical[destination],
        )
        for origin, destination in arcs
    }
    time_big_m = {
        (origin, destination): max(
            0.0,
            latest[origin]
            + duration[origin]
            + distance[origin, destination]
            - earliest[destination],
        )
        for origin, destination in customer_arcs
    }
    departure_big_m = {
        node: max(
            0.0,
            earliest[0] + duration[0] + distance[0, node] - earliest[node],
        )
        for node in customers
    }
    return_big_m = {
        node: max(
            0.0,
            latest[node] + duration[node] + distance[node, 0] - latest[0],
        )
        for node in customers
    }

    model = pyo.ConcreteModel()
    model.node_set = pyo.Set(initialize=nodes, ordered=True)
    model.customer_set = pyo.Set(initialize=customers, ordered=True)
    model.arc_set = pyo.Set(dimen=2, initialize=arcs)
    model.customer_arc_set = pyo.Set(dimen=2, initialize=customer_arcs)

    model.route_arc = pyo.Var(model.arc_set, domain=pyo.Binary)
    model.service_start = pyo.Var(
        model.customer_set,
        domain=pyo.Reals,
        bounds=lambda mdl, node: (earliest[node], latest[node]),
    )
    model.cumulative_load = pyo.Var(
        model.customer_set,
        domain=pyo.Reals,
        bounds=lambda mdl, node: (demand[node], capacity),
    )
    model.route_position = pyo.Var(
        model.customer_set,
        domain=pyo.Reals,
        bounds=(1, max(1, customer_count)),
    )
    model.zero_anchor = pyo.Var(domain=pyo.Reals, bounds=(0, 0))

    def outgoing_rule(mdl, node):
        return sum(
            mdl.route_arc[node, destination]
            for destination in nodes
            if destination != node
        ) == 1

    def incoming_rule(mdl, node):
        return sum(
            mdl.route_arc[origin, node]
            for origin in nodes
            if origin != node
        ) == 1

    model.customer_outgoing = pyo.Constraint(
        model.customer_set, rule=outgoing_rule
    )
    model.customer_incoming = pyo.Constraint(
        model.customer_set, rule=incoming_rule
    )
    model.depot_balance = pyo.Constraint(
        expr=(
            sum(model.route_arc[0, node] for node in customers)
            - sum(model.route_arc[node, 0] for node in customers)
            == model.zero_anchor
        )
    )

    def capacity_rule(mdl, origin, destination):
        return (
            mdl.cumulative_load[destination]
            >= mdl.cumulative_load[origin]
            + demand[destination]
            - capacity * (1 - mdl.route_arc[origin, destination])
        )

    def position_rule(mdl, origin, destination):
        return (
            mdl.route_position[destination]
            >= mdl.route_position[origin]
            + 1
            - customer_count * (1 - mdl.route_arc[origin, destination])
        )

    def customer_time_rule(mdl, origin, destination):
        return (
            mdl.service_start[destination]
            >= mdl.service_start[origin]
            + duration[origin]
            + distance[origin, destination]
            - time_big_m[origin, destination]
            * (1 - mdl.route_arc[origin, destination])
        )

    def departure_time_rule(mdl, node):
        return (
            mdl.service_start[node]
            >= earliest[0]
            + duration[0]
            + distance[0, node]
            - departure_big_m[node] * (1 - mdl.route_arc[0, node])
        )

    def return_time_rule(mdl, node):
        return (
            mdl.service_start[node] + duration[node] + distance[node, 0]
            <= latest[0]
            + return_big_m[node] * (1 - mdl.route_arc[node, 0])
        )

    model.capacity_propagation = pyo.Constraint(
        model.customer_arc_set, rule=capacity_rule
    )
    model.subtour_elimination = pyo.Constraint(
        model.customer_arc_set, rule=position_rule
    )
    model.customer_time_propagation = pyo.Constraint(
        model.customer_arc_set, rule=customer_time_rule
    )
    model.depot_departure_time = pyo.Constraint(
        model.customer_set, rule=departure_time_rule
    )
    model.depot_return_time = pyo.Constraint(
        model.customer_set, rule=return_time_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            distance[origin, destination]
            * model.route_arc[origin, destination]
            for origin, destination in arcs
        )
        + model.zero_anchor,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        if "no solution can be loaded" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
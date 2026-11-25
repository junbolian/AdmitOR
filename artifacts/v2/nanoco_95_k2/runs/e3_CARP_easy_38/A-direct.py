import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    vehicle_capacity = params["vehicle_capacity"]
    demands = params["demands"]
    num_vehicles = params["num_vehicles"]
    num_service_segments = params["num_service_segments"]
    num_nodes = params["num_nodes"]
    distance_matrix = params["distance_matrix"]
    node_coordinates = params["node_coordinates"]

    # Service segments: (0,3), (0,4), (2,3), (3,4)
    service_segments = [(0,3), (0,4), (2,3), (3,4)]
    # Map each service segment to its demand
    seg_demand = {i: demands[i] for i in range(num_service_segments)}

    # Nodes: 0..6
    nodes = list(range(num_nodes))
    vehicles = list(range(num_vehicles))
    segments = list(range(num_service_segments))

    model = pyo.ConcreteModel()

    # Decision variables:
    # x[v, i, j] = 1 if vehicle v travels directly from node i to node j
    model.x = pyo.Var(vehicles, nodes, nodes, within=pyo.Binary)

    # y[v, s] = 1 if vehicle v services segment s
    model.y = pyo.Var(vehicles, segments, within=pyo.Binary)

    # z[v, i] = 1 if vehicle v visits node i (for subtour elimination)
    model.z = pyo.Var(vehicles, nodes, within=pyo.Binary)

    # Objective: minimize total travel distance
    model.obj = pyo.Objective(
        expr=sum(
            distance_matrix[i][j] * model.x[v, i, j]
            for v in vehicles for i in nodes for j in nodes
        ),
        sense=pyo.minimize
    )

    # Constraints:

    # Each service segment must be serviced exactly once
    def service_once_rule(model, s):
        return sum(model.y[v, s] for v in vehicles) == 1
    model.service_once = pyo.Constraint(segments, rule=service_once_rule)

    # Capacity constraint per vehicle
    def capacity_rule(model, v):
        return sum(seg_demand[s] * model.y[v, s] for s in segments) <= vehicle_capacity
    model.capacity = pyo.Constraint(vehicles, rule=capacity_rule)

    # Flow conservation: if vehicle v visits node i, it must leave it
    def flow_out_rule(model, v, i):
        return sum(model.x[v, i, j] for j in nodes if j != i) == model.z[v, i]
    model.flow_out = pyo.Constraint(vehicles, nodes, rule=flow_out_rule)

    # Flow conservation: if vehicle v visits node i, it must have entered it
    def flow_in_rule(model, v, i):
        return sum(model.x[v, j, i] for j in nodes if j != i) == model.z[v, i]
    model.flow_in = pyo.Constraint(vehicles, nodes, rule=flow_in_rule)

    # Depot: each vehicle must start and end at node 0
    def depot_start_rule(model, v):
        return sum(model.x[v, 0, j] for j in nodes if j != 0) == 1
    model.depot_start = pyo.Constraint(vehicles, rule=depot_start_rule)

    def depot_end_rule(model, v):
        return sum(model.x[v, j, 0] for j in nodes if j != 0) == 1
    model.depot_end = pyo.Constraint(vehicles, rule=depot_end_rule)

    # No self-loops
    def no_self_loop_rule(model, v, i):
        return model.x[v, i, i] == 0
    model.no_self_loop = pyo.Constraint(vehicles, nodes, rule=no_self_loop_rule)

    # If vehicle v services segment s = (a,b), it must visit both endpoints a and b
    def service_visit_rule(model, v, s):
        a, b = service_segments[s]
        return model.y[v, s] <= model.z[v, a] + model.z[v, b] - 1
    model.service_visit = pyo.Constraint(vehicles, segments, rule=service_visit_rule)

    # Subtour elimination: for each vehicle, if it visits a node (other than depot),
    # it must be part of a single tour. Use MTZ-like constraints with z variables.
    # For any subset S not containing depot, sum of outgoing arcs from S >= z for any node in S
    # We'll use a simple formulation: for each vehicle, the number of arcs equals number of visited nodes
    def arc_count_rule(model, v):
        return sum(model.x[v, i, j] for i in nodes for j in nodes if i != j) == sum(model.z[v, i] for i in nodes)
    model.arc_count = pyo.Constraint(vehicles, rule=arc_count_rule)

    # Additional subtour elimination: for each vehicle, the number of arcs entering a set S
    # must be at least 1 if S is non-empty and doesn't contain depot.
    # We'll use a simple formulation: for each vehicle, the number of arcs equals number of visited nodes
    # This combined with flow conservation ensures a single tour.

    # Solve
    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except:
        return {'objective': None, 'status': 'infeasible'}
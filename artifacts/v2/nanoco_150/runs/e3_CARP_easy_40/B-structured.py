# IR: {
#   "sets": {"V": "range(num_nodes)", "K": "range(num_trucks)", "R": "range(num_mandatory_segments)", "O": "[0,1]", "A": "[(i,j) for i,j in V if i!=j]", "segments": "[[0,3],[0,4],[2,6],[5,7]]"},
#   "params": ["truck_capacity", "num_trucks", "demand_segment_0_3", "demand_segment_0_4", "demand_segment_2_6", "demand_segment_5_7", "distance_matrix", "num_nodes", "num_mandatory_segments"],
#   "variables": {"x[k,i,j]": "nonnegative integer traversal count", "y[k,r,o]": "binary service assignment and direction", "f[k,i,j]": "nonnegative continuous connectivity flow"},
#   "derived": {"b[k,v]": "sum(y[k,r,o] for r incident to v for o in O), v!=0", "B[k]": "sum(b[k,v] for v!=0)", "orientation": "0 uses listed segment direction; 1 reverses it"},
#   "constraints": [
#     "For each r: sum(y[k,r,o] for k in K for o in O)=1.",
#     "For each k: sum(y[k,r,o] for r in R for o in O)>=1.",
#     "For each k: sum(demand[r]*y[k,r,o] for r in R for o in O)<=truck_capacity.",
#     "For each k,r,o with oriented endpoints (i,j): x[k,i,j]>=y[k,r,o].",
#     "For each k,v: sum(x[k,v,j] for j!=v)=sum(x[k,i,v] for i!=v).",
#     "For each k,(i,j): f[k,i,j]<=2*num_mandatory_segments*x[k,i,j].",
#     "For each k,v!=0: sum(f[k,i,v] for i!=v)-sum(f[k,v,j] for j!=v)=b[k,v].",
#     "For each k: sum(f[k,0,j] for j!=0)-sum(f[k,i,0] for i!=0)=B[k]."
#   ],
#   "objective": "minimize sum(distance_matrix[i][j]*x[k,i,j] for k in K for (i,j) in A)"
# }

import math
import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    truck_capacity = float(params["truck_capacity"])
    num_trucks = operator.index(params["num_trucks"])
    num_nodes = operator.index(params["num_nodes"])
    num_mandatory_segments = operator.index(
        params["num_mandatory_segments"]
    )
    demands = (
        float(params["demand_segment_0_3"]),
        float(params["demand_segment_0_4"]),
        float(params["demand_segment_2_6"]),
        float(params["demand_segment_5_7"]),
    )
    raw_distances = params["distance_matrix"]

    segments = ((0, 3), (0, 4), (2, 6), (5, 7))
    depot = 0

    if (
        num_nodes != 8
        or num_mandatory_segments != len(segments)
        or num_trucks < 1
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    if len(raw_distances) != num_nodes or any(
        len(row) != num_nodes for row in raw_distances
    ):
        return {"objective": None, "status": "invalid_distance_matrix"}

    distances = tuple(
        tuple(float(value) for value in row)
        for row in raw_distances
    )
    if (
        not math.isfinite(truck_capacity)
        or truck_capacity < 0
        or any(not math.isfinite(value) or value < 0 for value in demands)
        or any(
            not math.isfinite(value) or value < 0
            for row in distances
            for value in row
        )
    ):
        return {"objective": None, "status": "invalid_numeric_parameters"}

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.trucks = pyo.Set(initialize=range(num_trucks), ordered=True)
    model.tasks = pyo.Set(
        initialize=range(num_mandatory_segments), ordered=True
    )
    model.orientations = pyo.Set(initialize=(0, 1), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
    )
    model.non_depot_nodes = pyo.Set(
        initialize=(
            node for node in range(num_nodes) if node != depot
        )
    )

    model.capacity = pyo.Param(initialize=truck_capacity)
    model.salt_demand = pyo.Param(
        model.tasks,
        initialize={task: demands[task] for task in model.tasks},
    )
    model.travel_distance = pyo.Param(
        model.arcs,
        initialize={
            (i, j): distances[i][j] for i, j in model.arcs
        },
    )

    model.x = pyo.Var(
        model.trucks, model.arcs, domain=pyo.NonNegativeIntegers
    )
    model.y = pyo.Var(
        model.trucks,
        model.tasks,
        model.orientations,
        domain=pyo.Binary,
    )
    model.f = pyo.Var(
        model.trucks, model.arcs, domain=pyo.NonNegativeReals
    )

    def endpoint_requirement_rule(instance, truck, node):
        return sum(
            instance.y[truck, task, orientation]
            for task in instance.tasks
            if node in segments[task]
            for orientation in instance.orientations
        )

    model.endpoint_requirement = pyo.Expression(
        model.trucks,
        model.non_depot_nodes,
        rule=endpoint_requirement_rule,
    )

    def total_requirement_rule(instance, truck):
        return sum(
            instance.endpoint_requirement[truck, node]
            for node in instance.non_depot_nodes
        )

    model.total_requirement = pyo.Expression(
        model.trucks, rule=total_requirement_rule
    )

    def service_once_rule(instance, task):
        return sum(
            instance.y[truck, task, orientation]
            for truck in instance.trucks
            for orientation in instance.orientations
        ) == 1

    model.service_once = pyo.Constraint(
        model.tasks, rule=service_once_rule
    )

    def nonempty_route_rule(instance, truck):
        return sum(
            instance.y[truck, task, orientation]
            for task in instance.tasks
            for orientation in instance.orientations
        ) >= 1

    model.nonempty_route = pyo.Constraint(
        model.trucks, rule=nonempty_route_rule
    )

    def salt_capacity_rule(instance, truck):
        return sum(
            instance.salt_demand[task]
            * instance.y[truck, task, orientation]
            for task in instance.tasks
            for orientation in instance.orientations
        ) <= instance.capacity

    model.salt_capacity = pyo.Constraint(
        model.trucks, rule=salt_capacity_rule
    )

    def service_traversal_rule(instance, truck, task, orientation):
        first, second = segments[task]
        if orientation == 1:
            first, second = second, first
        return (
            instance.x[truck, first, second]
            >= instance.y[truck, task, orientation]
        )

    model.service_traversal = pyo.Constraint(
        model.trucks,
        model.tasks,
        model.orientations,
        rule=service_traversal_rule,
    )

    def traversal_balance_rule(instance, truck, node):
        return sum(
            instance.x[truck, node, other]
            for other in instance.nodes
            if other != node
        ) == sum(
            instance.x[truck, other, node]
            for other in instance.nodes
            if other != node
        )

    model.traversal_balance = pyo.Constraint(
        model.trucks, model.nodes, rule=traversal_balance_rule
    )

    def flow_link_rule(instance, truck, first, second):
        return (
            instance.f[truck, first, second]
            <= 2 * num_mandatory_segments
            * instance.x[truck, first, second]
        )

    model.flow_link = pyo.Constraint(
        model.trucks, model.arcs, rule=flow_link_rule
    )

    def endpoint_flow_rule(instance, truck, node):
        incoming = sum(
            instance.f[truck, other, node]
            for other in instance.nodes
            if other != node
        )
        outgoing = sum(
            instance.f[truck, node, other]
            for other in instance.nodes
            if other != node
        )
        return (
            incoming - outgoing
            == instance.endpoint_requirement[truck, node]
        )

    model.endpoint_flow = pyo.Constraint(
        model.trucks,
        model.non_depot_nodes,
        rule=endpoint_flow_rule,
    )

    def depot_flow_rule(instance, truck):
        outgoing = sum(
            instance.f[truck, depot, node]
            for node in instance.non_depot_nodes
        )
        incoming = sum(
            instance.f[truck, node, depot]
            for node in instance.non_depot_nodes
        )
        return outgoing - incoming == instance.total_requirement[truck]

    model.depot_flow = pyo.Constraint(
        model.trucks, rule=depot_flow_rule
    )

    # Integer balanced traversals form closed directed walks. Connectivity
    # flow connects every serviced endpoint to the depot. Any disconnected
    # component therefore contains no service and can be discarded without
    # increasing cost because all travel distances are nonnegative.
    # Traversing a required segment without servicing it is deadheading.
    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[truck, i, j]
            for truck in model.trucks
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
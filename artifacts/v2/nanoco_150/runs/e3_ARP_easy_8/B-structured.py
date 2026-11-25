# IR: {"sets":{"N":"range(num_nodes)","K":"range(num_vehicles)","R":"range(num_mandatory_segments)","A":"{(i,j) in N x N: i != j}"},"params":{"distance_matrix":"travel costs on A","mandatory_segments":"undirected endpoint pairs (u[r],v[r]) for r in R","num_nodes":"number of nodes","num_mandatory_segments":"number of required segments","num_vehicles":"fleet size","depot":"dispatch node","B":"2*num_mandatory_segments"},"variables":{"x[k,i,j]":"nonnegative integer traversal count","q[k,r]":"binary service assignment","f[k,i,j]":"nonnegative continuous connectivity flow"},"constraints":["For each r: sum_k q[k,r] = 1.","For each k,r: x[k,u[r],v[r]] + x[k,v[r],u[r]] >= q[k,r].","For each k,i: sum_{j != i} x[k,i,j] = sum_{j != i} x[k,j,i].","For each k,(i,j): f[k,i,j] <= B*x[k,i,j].","For each k,i != depot: incoming f minus outgoing f = sum_r (1[u[r]=i]+1[v[r]=i])*q[k,r].","For each k: outgoing depot f minus incoming depot f = sum_r (1[u[r]!=depot]+1[v[r]!=depot])*q[k,r]."],"objective":"minimize sum_{k,(i,j) in A} distance_matrix[i][j]*x[k,i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    mandatory_segments = params["mandatory_segments"]
    num_nodes = params["num_nodes"]
    num_mandatory_segments = params["num_mandatory_segments"]
    num_vehicles = params["num_vehicles"]
    depot = params["depot"]

    if len(mandatory_segments) != num_mandatory_segments:
        raise ValueError("mandatory_segments cardinality does not match its parameter.")
    if len(distance_matrix) != num_nodes or any(
        len(row) != num_nodes for row in distance_matrix
    ):
        raise ValueError("distance_matrix dimensions do not match num_nodes.")
    if depot not in range(num_nodes):
        raise ValueError("depot is outside the node index set.")

    segment_endpoints = {}
    for segment_index in range(num_mandatory_segments):
        first_node, second_node = mandatory_segments[segment_index]
        if (
            first_node not in range(num_nodes)
            or second_node not in range(num_nodes)
            or first_node == second_node
        ):
            raise ValueError("Mandatory segments must join distinct valid nodes.")
        segment_endpoints[segment_index] = (first_node, second_node)

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.K = pyo.Set(initialize=range(num_vehicles), ordered=True)
    model.R = pyo.Set(
        initialize=range(num_mandatory_segments), ordered=True
    )
    model.A = pyo.Set(
        dimen=2,
        initialize=(
            (first_node, second_node)
            for first_node in range(num_nodes)
            for second_node in range(num_nodes)
            if first_node != second_node
        ),
        ordered=True,
    )

    model.travel_cost = pyo.Param(
        model.A,
        initialize=lambda mdl, first_node, second_node: distance_matrix[
            first_node
        ][second_node],
        within=pyo.NonNegativeReals,
    )
    model.flow_capacity = pyo.Param(
        initialize=2 * num_mandatory_segments,
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.K, model.A, domain=pyo.NonNegativeIntegers)
    model.q = pyo.Var(model.K, model.R, domain=pyo.Binary)
    model.f = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)

    def assignment_rule(mdl, segment_index):
        return (
            pyo.quicksum(
                mdl.q[vehicle_index, segment_index]
                for vehicle_index in mdl.K
            )
            == 1
        )

    model.service_assignment = pyo.Constraint(
        model.R, rule=assignment_rule
    )

    def service_rule(mdl, vehicle_index, segment_index):
        first_node, second_node = segment_endpoints[segment_index]
        return (
            mdl.x[vehicle_index, first_node, second_node]
            + mdl.x[vehicle_index, second_node, first_node]
            >= mdl.q[vehicle_index, segment_index]
        )

    model.required_service = pyo.Constraint(
        model.K, model.R, rule=service_rule
    )

    def traversal_balance_rule(mdl, vehicle_index, node):
        if num_nodes == 1:
            return pyo.Constraint.Feasible
        return pyo.quicksum(
            mdl.x[vehicle_index, node, neighbor]
            for neighbor in mdl.N
            if neighbor != node
        ) == pyo.quicksum(
            mdl.x[vehicle_index, neighbor, node]
            for neighbor in mdl.N
            if neighbor != node
        )

    model.traversal_balance = pyo.Constraint(
        model.K, model.N, rule=traversal_balance_rule
    )

    def flow_link_rule(mdl, vehicle_index, first_node, second_node):
        return (
            mdl.f[vehicle_index, first_node, second_node]
            <= mdl.flow_capacity
            * mdl.x[vehicle_index, first_node, second_node]
        )

    model.connectivity_capacity = pyo.Constraint(
        model.K, model.A, rule=flow_link_rule
    )

    def connectivity_balance_rule(mdl, vehicle_index, node):
        if num_nodes == 1:
            return pyo.Constraint.Feasible

        incoming = pyo.quicksum(
            mdl.f[vehicle_index, neighbor, node]
            for neighbor in mdl.N
            if neighbor != node
        )
        outgoing = pyo.quicksum(
            mdl.f[vehicle_index, node, neighbor]
            for neighbor in mdl.N
            if neighbor != node
        )

        if node == depot:
            total_demand = pyo.quicksum(
                (
                    int(segment_endpoints[segment_index][0] != depot)
                    + int(segment_endpoints[segment_index][1] != depot)
                )
                * mdl.q[vehicle_index, segment_index]
                for segment_index in mdl.R
            )
            return outgoing - incoming == total_demand

        node_demand = pyo.quicksum(
            (
                int(segment_endpoints[segment_index][0] == node)
                + int(segment_endpoints[segment_index][1] == node)
            )
            * mdl.q[vehicle_index, segment_index]
            for segment_index in mdl.R
        )
        return incoming - outgoing == node_demand

    model.connectivity_balance = pyo.Constraint(
        model.K, model.N, rule=connectivity_balance_rule
    )

    model.total_distance = pyo.Objective(
        expr=pyo.quicksum(
            model.travel_cost[first_node, second_node]
            * model.x[vehicle_index, first_node, second_node]
            for vehicle_index in model.K
            for first_node, second_node in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
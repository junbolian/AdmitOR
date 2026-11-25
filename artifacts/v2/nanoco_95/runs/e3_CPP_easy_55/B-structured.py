# IR: {"sets":{"V":"{0,...,num_nodes-1}","R":[[0,1],[0,2],[1,3],[2,6],[3,4],[3,5],[3,6],[5,6]],"P":"{(i,j): i,j in V, i<j}"},"params":{"edge_cost_{i}_{j}":"nonnegative service cost for each (i,j) in R","deadhead_cost_{i}_{j}":"nonnegative deadhead cost for each (i,j) in P","num_nodes":"frozen node count","num_graph_edges":"frozen graph-edge count","num_required_edges":"frozen required-edge count","garage_node":"frozen depot index"},"variables":{"deadhead_count[P]":"nonnegative integer","half_degree[V]":"nonnegative integer"},"constraints":["Validate frozen counts against the specified topology and garage_node against node 0.","For each v in V: required_degree[v] + sum(deadhead_count[i,j] for incident (i,j) in P) = 2*half_degree[v]."],"objective":"Minimize sum(edge_cost[i,j] for (i,j) in R) + sum(deadhead_cost[i,j]*deadhead_count[i,j] for (i,j) in P)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    required_edges = (
        (0, 1),
        (0, 2),
        (1, 3),
        (2, 6),
        (3, 4),
        (3, 5),
        (3, 6),
        (5, 6),
    )

    service_costs = {
        (0, 1): params["edge_cost_0_1"],
        (0, 2): params["edge_cost_0_2"],
        (1, 3): params["edge_cost_1_3"],
        (2, 6): params["edge_cost_2_6"],
        (3, 4): params["edge_cost_3_4"],
        (3, 5): params["edge_cost_3_5"],
        (3, 6): params["edge_cost_3_6"],
        (5, 6): params["edge_cost_5_6"],
    }

    deadhead_costs = {
        (0, 1): params["deadhead_cost_0_1"],
        (0, 2): params["deadhead_cost_0_2"],
        (0, 3): params["deadhead_cost_0_3"],
        (0, 4): params["deadhead_cost_0_4"],
        (0, 5): params["deadhead_cost_0_5"],
        (0, 6): params["deadhead_cost_0_6"],
        (1, 2): params["deadhead_cost_1_2"],
        (1, 3): params["deadhead_cost_1_3"],
        (1, 4): params["deadhead_cost_1_4"],
        (1, 5): params["deadhead_cost_1_5"],
        (1, 6): params["deadhead_cost_1_6"],
        (2, 3): params["deadhead_cost_2_3"],
        (2, 4): params["deadhead_cost_2_4"],
        (2, 5): params["deadhead_cost_2_5"],
        (2, 6): params["deadhead_cost_2_6"],
        (3, 4): params["deadhead_cost_3_4"],
        (3, 5): params["deadhead_cost_3_5"],
        (3, 6): params["deadhead_cost_3_6"],
        (4, 5): params["deadhead_cost_4_5"],
        (4, 6): params["deadhead_cost_4_6"],
        (5, 6): params["deadhead_cost_5_6"],
    }

    num_nodes = params["num_nodes"]
    num_graph_edges = params["num_graph_edges"]
    num_required_edges = params["num_required_edges"]
    garage_node = params["garage_node"]

    topology_nodes = tuple(
        sorted({endpoint for edge in required_edges for endpoint in edge})
    )
    if (
        num_nodes != len(topology_nodes)
        or num_graph_edges != len(required_edges)
        or num_required_edges != len(required_edges)
        or garage_node != topology_nodes[0]
    ):
        return {"objective": None, "status": "invalid_structure"}

    nodes = topology_nodes
    node_pairs = tuple(
        (first_node, second_node)
        for first_node in nodes
        for second_node in nodes
        if first_node < second_node
    )
    required_degrees = {
        node: sum(
            1
            for first_node, second_node in required_edges
            if node == first_node or node == second_node
        )
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=nodes, ordered=True)
    model.required_edges = pyo.Set(
        dimen=2, initialize=required_edges, ordered=True
    )
    model.travel_pairs = pyo.Set(
        dimen=2, initialize=node_pairs, ordered=True
    )

    model.service_cost = pyo.Param(
        model.required_edges,
        initialize=service_costs,
        within=pyo.NonNegativeReals,
    )
    model.deadhead_cost = pyo.Param(
        model.travel_pairs,
        initialize=deadhead_costs,
        within=pyo.NonNegativeReals,
    )
    model.required_degree = pyo.Param(
        model.vertices,
        initialize=required_degrees,
        within=pyo.NonNegativeIntegers,
    )
    model.depot_node = pyo.Param(
        initialize=garage_node, within=model.vertices
    )

    model.deadhead_count = pyo.Var(
        model.travel_pairs, domain=pyo.NonNegativeIntegers
    )
    model.half_degree = pyo.Var(
        model.vertices, domain=pyo.NonNegativeIntegers
    )

    # Each required edge contributes one fixed service traversal.
    # These edges already form a connected spanning graph containing the
    # garage. Making every degree even therefore guarantees an Euler tour
    # starting and ending at the garage. Orienting that tour gives equal
    # incoming and outgoing traversal counts at every node.
    def even_degree_rule(instance, node):
        return (
            instance.required_degree[node]
            + sum(
                instance.deadhead_count[first_node, second_node]
                for first_node, second_node in instance.travel_pairs
                if node == first_node or node == second_node
            )
            == 2 * instance.half_degree[node]
        )

    model.even_degree_constraints = pyo.Constraint(
        model.vertices, rule=even_degree_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.service_cost[first_node, second_node]
                for first_node, second_node in model.required_edges
            )
            + sum(
                model.deadhead_cost[first_node, second_node]
                * model.deadhead_count[first_node, second_node]
                for first_node, second_node in model.travel_pairs
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
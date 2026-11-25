# IR: {"sets":{"N":"range(num_nodes)","E":"range(num_candidate_edges)","I[i]":"candidate-edge indices incident to node i","K[i]":"range(len(I[i])+1)"},"params":{"num_nodes":"params[num_nodes]","num_candidate_edges":"params[num_candidate_edges]","candidate_edges":"params[candidate_edges]","leaf_reward":"params[leaf_reward]","leaf_degree_target":"params[leaf_degree_target]","node_coords":"params[node_coords], reference metadata","node_i_x,node_i_y":"params[node_i_x],params[node_i_y] for i=0,...,11; geographic metadata","distance_matrix":"params[distance_matrix], reference metadata"},"variables":{"selected[e]":"binary","flow_forward[e]":"nonnegative continuous, first endpoint to second","flow_reverse[e]":"nonnegative continuous, second endpoint to first","degree_choice[i,k]":"binary; 1 iff node i has degree k"},"constraints":["sum(selected[e] for e in E)=num_nodes-1","flow_forward[e]<=(num_nodes-1)*selected[e] for e in E","flow_reverse[e]<=(num_nodes-1)*selected[e] for e in E","outflow[i]-inflow[i]=num_nodes-1 if i=0, otherwise -1","sum(degree_choice[i,k] for k in K[i])=1 for i in N","sum(k*degree_choice[i,k] for k in K[i])=sum(selected[e] for e in I[i]) for i in N"],"objective":"maximize leaf_reward*sum(degree_choice[i,k] for i in N for k in K[i] if k==leaf_degree_target); geographic metadata imposes no costs or constraints"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_candidate_edges = params["num_candidate_edges"]
    candidate_edges = tuple(tuple(edge) for edge in params["candidate_edges"])
    leaf_reward = params["leaf_reward"]
    leaf_degree_target = params["leaf_degree_target"]

    # Read all geographic inputs. They do not affect this purely topological
    # objective, and the problem specifies no distance-based constraints.
    node_coords = params["node_coords"]
    coordinate_components = (
        (params["node_0_x"], params["node_0_y"]),
        (params["node_1_x"], params["node_1_y"]),
        (params["node_2_x"], params["node_2_y"]),
        (params["node_3_x"], params["node_3_y"]),
        (params["node_4_x"], params["node_4_y"]),
        (params["node_5_x"], params["node_5_y"]),
        (params["node_6_x"], params["node_6_y"]),
        (params["node_7_x"], params["node_7_y"]),
        (params["node_8_x"], params["node_8_y"]),
        (params["node_9_x"], params["node_9_y"]),
        (params["node_10_x"], params["node_10_y"]),
        (params["node_11_x"], params["node_11_y"]),
    )
    distance_matrix = params["distance_matrix"]

    if num_nodes != 12:
        raise ValueError("The fixed network must contain exactly 12 nodes.")
    if len(candidate_edges) != num_candidate_edges:
        raise ValueError("num_candidate_edges does not match candidate_edges.")

    nodes = tuple(range(num_nodes))
    edge_indices = tuple(range(num_candidate_edges))
    incident = {node: [] for node in nodes}
    outgoing_forward = {node: [] for node in nodes}
    incoming_forward = {node: [] for node in nodes}
    seen_edges = set()

    for edge_id, endpoints in enumerate(candidate_edges):
        if len(endpoints) != 2:
            raise ValueError("Each candidate edge must have two endpoints.")
        first, second = endpoints
        if first not in incident or second not in incident or first == second:
            raise ValueError("Candidate edges must join two distinct valid nodes.")

        undirected_edge = frozenset(endpoints)
        if undirected_edge in seen_edges:
            raise ValueError("Candidate edges must be unique undirected edges.")
        seen_edges.add(undirected_edge)

        incident[first].append(edge_id)
        incident[second].append(edge_id)
        outgoing_forward[first].append(edge_id)
        incoming_forward[second].append(edge_id)

    degree_options = {
        node: tuple(range(len(incident[node]) + 1)) for node in nodes
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.E = pyo.Set(initialize=edge_indices, ordered=True)
    model.degree_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (node, degree)
            for node in nodes
            for degree in degree_options[node]
        ],
        ordered=True,
    )

    model.selected = pyo.Var(model.E, domain=pyo.Binary)
    model.flow_forward = pyo.Var(model.E, domain=pyo.NonNegativeReals)
    model.flow_reverse = pyo.Var(model.E, domain=pyo.NonNegativeReals)
    model.degree_choice = pyo.Var(model.degree_pairs, domain=pyo.Binary)

    model.tree_edge_count = pyo.Constraint(
        expr=sum(model.selected[edge_id] for edge_id in model.E)
        == num_nodes - 1
    )

    def forward_capacity_rule(current_model, edge_id):
        return (
            current_model.flow_forward[edge_id]
            <= (num_nodes - 1) * current_model.selected[edge_id]
        )

    def reverse_capacity_rule(current_model, edge_id):
        return (
            current_model.flow_reverse[edge_id]
            <= (num_nodes - 1) * current_model.selected[edge_id]
        )

    model.forward_capacity = pyo.Constraint(
        model.E, rule=forward_capacity_rule
    )
    model.reverse_capacity = pyo.Constraint(
        model.E, rule=reverse_capacity_rule
    )

    def flow_balance_rule(current_model, node):
        net_outflow = sum(
            current_model.flow_forward[edge_id]
            - current_model.flow_reverse[edge_id]
            for edge_id in outgoing_forward[node]
        ) + sum(
            current_model.flow_reverse[edge_id]
            - current_model.flow_forward[edge_id]
            for edge_id in incoming_forward[node]
        )
        supply = num_nodes - 1 if node == 0 else -1
        return net_outflow == supply

    # Root flow makes every node reachable through selected edges.
    # Connectivity together with exactly num_nodes - 1 edges gives a tree.
    model.flow_balance = pyo.Constraint(model.N, rule=flow_balance_rule)

    def one_degree_rule(current_model, node):
        return sum(
            current_model.degree_choice[node, degree]
            for degree in degree_options[node]
        ) == 1

    def degree_link_rule(current_model, node):
        return sum(
            degree * current_model.degree_choice[node, degree]
            for degree in degree_options[node]
        ) == sum(
            current_model.selected[edge_id]
            for edge_id in incident[node]
        )

    # Exact degree classification remains valid for negative rewards and for
    # targets other than one, including zero and noninteger targets.
    model.one_degree = pyo.Constraint(model.N, rule=one_degree_rule)
    model.degree_link = pyo.Constraint(model.N, rule=degree_link_rule)

    model.total_reward = pyo.Objective(
        expr=leaf_reward
        * sum(
            model.degree_choice[node, degree]
            for node in nodes
            for degree in degree_options[node]
            if degree == leaf_degree_target
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no feasible solution is available to load.
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_reward))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
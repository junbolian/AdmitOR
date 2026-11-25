# IR: {"sets":{"V":"range(params['num_nodes'])","E":"distinct canonical undirected pairs (min(u,v),max(u,v)) from params['edges']"},"params":{"edges":"allowed undirected trading edges","num_nodes":"number of nodes"},"variables":{"selected[u,v]":"Binary for (u,v) in E"},"constraints":["For each i in V: sum(selected[u,v] for (u,v) in E if i in (u,v)) <= 1."],"objective":"Maximize sum(selected[u,v] for (u,v) in E)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    edges = params["edges"]

    canonical_edges = set()
    for node_u, node_v in edges:
        if not (0 <= node_u < num_nodes and 0 <= node_v < num_nodes):
            raise ValueError("Edge endpoints must belong to the node set.")
        if node_u == node_v:
            raise ValueError("Trading edges must connect distinct nodes.")
        canonical_edges.add((min(node_u, node_v), max(node_u, node_v)))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.trading_edges = pyo.Set(
        initialize=sorted(canonical_edges), dimen=2, ordered=True
    )
    model.selected = pyo.Var(model.trading_edges, domain=pyo.Binary)

    incident_edges = {node: [] for node in range(num_nodes)}
    for node_u, node_v in canonical_edges:
        incident_edges[node_u].append((node_u, node_v))
        incident_edges[node_v].append((node_u, node_v))

    def participation_rule(instance, node):
        expression = pyo.quicksum(
            instance.selected[node_u, node_v]
            for node_u, node_v in incident_edges[node]
        )
        # Tuple form also supports isolated nodes with an empty sum.
        return (None, expression, 1)

    model.participation_limit = pyo.Constraint(
        model.nodes, rule=participation_rule
    )
    model.matching_cardinality = pyo.Objective(
        expr=pyo.quicksum(
            model.selected[node_u, node_v]
            for node_u, node_v in model.trading_edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.matching_cardinality))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
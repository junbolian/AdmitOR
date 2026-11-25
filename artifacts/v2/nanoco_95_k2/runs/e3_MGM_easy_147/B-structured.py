# IR: {"sets":{"V":"range(params['num_nodes'])","E":"unique canonical undirected pairs from params['edges']"},"params":{"num_nodes":"number of nodes","edges":"allowed undirected edges"},"variables":{"x[e]":"Binary for e in E"},"constraints":["For every v in V: sum(x[e] for e incident to v) <= 1"],"objective":"maximize sum(x[e] for e in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    supplied_edges = params["edges"]

    nodes = range(num_nodes)
    edge_set = set()

    for first, second in supplied_edges:
        if first not in nodes or second not in nodes:
            raise ValueError("An edge endpoint is outside the node set.")
        if first == second:
            raise ValueError("Trading edges must connect distinct nodes.")
        edge_set.add((min(first, second), max(first, second)))

    edges = sorted(edge_set)
    incident_edges = {node: [] for node in nodes}
    for edge in edges:
        incident_edges[edge[0]].append(edge)
        incident_edges[edge[1]].append(edge)

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.trading_edges = pyo.Set(
        dimen=2,
        initialize=edges,
        within=model.nodes * model.nodes,
        ordered=True,
    )
    model.selected = pyo.Var(model.trading_edges, domain=pyo.Binary)

    def participation_rule(instance, node):
        return (
            None,
            pyo.quicksum(
                instance.selected[edge] for edge in incident_edges[node]
            ),
            1,
        )

    model.participation_limit = pyo.Constraint(
        model.nodes, rule=participation_rule
    )
    model.matching_size = pyo.Objective(
        expr=pyo.quicksum(
            model.selected[edge] for edge in model.trading_edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        message = str(error).lower()
        if (
            "feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.matching_size))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
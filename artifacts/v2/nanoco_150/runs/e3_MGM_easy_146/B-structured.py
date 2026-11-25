# IR: {"sets":{"V":"range(params['n_slots'])","E":"unique undirected pairs (min(u,v),max(u,v)) from params['edges']"},"params":{"n_slots":"number of vertices","edges":"allowed adjacency pairs"},"variables":{"x[e]":"binary for each e in E"},"constraints":["Each edge has distinct endpoints in V.","For every v in V: sum(x[e] for e incident to v) <= 1."],"objective":"maximize sum(x[e] for e in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_slots = params["n_slots"]
    edges = params["edges"]

    allowed_edges = set()
    for first, second in edges:
        if not (0 <= first < n_slots and 0 <= second < n_slots):
            raise ValueError("Edge endpoints must belong to the slot index set.")
        if first == second:
            raise ValueError("Pairing edges must have distinct endpoints.")
        allowed_edges.add((min(first, second), max(first, second)))

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=range(n_slots), ordered=True)
    model.allowed_edges = pyo.Set(
        initialize=sorted(allowed_edges),
        dimen=2,
        within=model.vertices * model.vertices,
        ordered=True,
    )
    model.selected = pyo.Var(model.allowed_edges, domain=pyo.Binary)

    incident_edges = {vertex: [] for vertex in model.vertices}
    for first, second in model.allowed_edges:
        incident_edges[first].append((first, second))
        incident_edges[second].append((first, second))

    def slot_capacity_rule(instance, vertex):
        # Tuple form also supports isolated vertices with an empty sum.
        return (
            None,
            pyo.quicksum(
                instance.selected[edge] for edge in incident_edges[vertex]
            ),
            1,
        )

    model.slot_capacity = pyo.Constraint(
        model.vertices,
        rule=slot_capacity_rule,
    )
    model.matching_cardinality = pyo.Objective(
        expr=pyo.quicksum(
            model.selected[edge] for edge in model.allowed_edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.matching_cardinality))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
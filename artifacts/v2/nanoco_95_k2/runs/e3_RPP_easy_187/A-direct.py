import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    required_edges = params["required_edges"]
    depot_node = params["depot_node"]
    num_nodes = params["num_nodes"]

    nodes = list(range(num_nodes))

    def cost(u, v):
        return distance_matrix[u * num_nodes + v]

    # Directed arcs (both directions for every pair), since routing is on a
    # fully connected network using the complete distance matrix.
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(
        initialize=[(u, v) for u in nodes for v in nodes if u != v],
        dimen=2,
        ordered=True,
    )
    # Required edges as node pairs (each must be traversed at least once).
    req_pairs = [(int(u), int(v)) for (u, v) in required_edges]

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(cost(u, v) * m.x[u, v] for (u, v) in m.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Flow conservation: arrivals == departures at every node.
    def flow_rule(m, k):
        inflow = sum(m.x[u, k] for u in nodes if u != k)
        outflow = sum(m.x[k, v] for v in nodes if v != k)
        return inflow == outflow

    model.flow_con = pyo.Constraint(model.nodes, rule=flow_rule)

    # Depot must have at least one departure (route is non-empty).
    def depot_rule(m):
        return sum(m.x[depot_node, v] for v in nodes if v != depot_node) >= 1

    model.depot_con = pyo.Constraint(rule=depot_rule)

    # Each required edge must be serviced at least once (in either direction).
    def req_rule(m, idx):
        u, v = req_pairs[idx]
        return m.x[u, v] + m.x[v, u] >= 1

    model.required_con = pyo.Constraint(
        range(len(req_pairs)), rule=req_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
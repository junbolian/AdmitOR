import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    node_coords = params["node_coords"]
    num_graph_edges = int(params["num_graph_edges"])
    num_required_edges = int(params["num_required_edges"])
    service_costs = params["service_costs"]
    travel_cost_matrix = params["travel_cost_matrix"]

    required_edges = [
        (0, 1), (0, 2), (1, 3), (2, 6),
        (3, 4), (3, 5), (3, 6), (5, 6),
    ]

    num_nodes = len(node_coords)
    nodes = list(range(num_nodes))
    edge_idx = list(range(len(required_edges)))

    model = pyo.ConcreteModel()

    # Deadhead arcs between distinct nodes
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    # f[i,j]: number of deadhead traversals from i to j
    model.f = pyo.Var(arcs, domain=pyo.NonNegativeIntegers)
    # z[k]: forward-direction service traversals of required edge k
    model.z = pyo.Var(edge_idx, domain=pyo.NonNegativeIntegers)
    # w[k]: reverse-direction service traversals of required edge k
    model.w = pyo.Var(edge_idx, domain=pyo.NonNegativeIntegers)

    def cost_rule(mdl):
        return (
            sum(travel_cost_matrix[i][j] * mdl.f[i, j] for (i, j) in arcs)
            + sum(service_costs[k] * (mdl.z[k] + mdl.w[k]) for k in edge_idx)
        )

    model.obj = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def flow_rule(mdl, v):
        entry = sum(mdl.f[i, v] for i in nodes if i != v)
        leave = sum(mdl.f[v, j] for j in nodes if j != v)
        for k in edge_idx:
            i, j = required_edges[k]
            # forward service arc i->j
            if j == v:
                entry += mdl.z[k]
            if i == v:
                leave += mdl.z[k]
            # reverse service arc j->i
            if i == v:
                entry += mdl.w[k]
            if j == v:
                leave += mdl.w[k]
        return entry == leave

    model.flow_con = pyo.Constraint(nodes, rule=flow_rule)

    def cover_rule(mdl, k):
        return mdl.z[k] + mdl.w[k] >= 1

    model.cover_con = pyo.Constraint(edge_idx, rule=cover_rule)

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
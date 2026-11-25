import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = 7
    num_edges = int(params["num_graph_edges"])
    num_required = int(params["num_required_edges"])

    num_graph_edges = 8
    num_required_edges = 8

    required_edges = [
        (0, 1), (0, 2), (1, 3), (2, 6),
        (3, 4), (3, 5), (3, 6), (5, 6),
    ]
    service_costs = list(params["service_costs"])
    travel_cost_matrix = params["travel_cost_matrix"]

    nodes = range(num_nodes)
    req_idx = range(num_required_edges)
    edge_nodes = list(nodes)

    model = pyo.ConcreteModel()

    # x[i,j]: number of deadhead traversals of arc (i,j)
    model.x = pyo.Var(edge_nodes, edge_nodes, within=pyo.NonNegativeIntegers)

    # y[k]: binary, required-edge k serviced exactly once (in its defined direction)
    # We service each required edge exactly once in reverse? We need orientation.
    # Model each required edge as serviced in one direction (u->v) or (v->u).
    # Use two binaries: forward and backward service.
    model.yf = pyo.Var(req_idx, within=pyo.Binary)
    model.yb = pyo.Var(req_idx, within=pyo.Binary)

    # Each required edge must be serviced at least once (exactly one direction once)
    model.service_req = pyo.Constraint(
        req_idx, rule=lambda m, k: m.yf[k] + m.yb[k] == 1
    )

    # Flow conservation at each node:
    # out - in = net service imbalance contributions
    # For each serviced edge k=(u,v): forward contributes +1 out of u, -1 out of v
    # backward contributes +1 out of v, -1 out of u
    def flow_rule(m, i):
        out_flow = sum(m.x[i, j] for j in nodes if j != i)
        in_flow = sum(m.x[j, i] for j in nodes if j != i)
        service_balance = 0
        for k in req_idx:
            u, v = required_edges[k]
            if u == i:
                service_balance += m.yf[k] - m.yb[k]
            if v == i:
                service_balance += m.yb[k] - m.yf[k]
        return out_flow - in_flow == service_balance

    model.flow_con = pyo.Constraint(nodes, rule=flow_rule)

    def objective_rule(m):
        deadhead = sum(
            travel_cost_matrix[i][j] * m.x[i, j]
            for i in nodes for j in nodes if i != j
        )
        service = sum(
            service_costs[k] * (m.yf[k] + m.yb[k]) for k in req_idx
        )
        return deadhead + service

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
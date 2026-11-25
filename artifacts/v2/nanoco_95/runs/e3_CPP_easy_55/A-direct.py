import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    garage_node = int(params["garage_node"])

    required_edges = [
        (0, 1), (0, 2), (1, 3), (2, 6), (3, 4), (3, 5), (3, 6), (5, 6)
    ]
    service_cost = {
        (0, 1): params["edge_cost_0_1"],
        (0, 2): params["edge_cost_0_2"],
        (1, 3): params["edge_cost_1_3"],
        (2, 6): params["edge_cost_2_6"],
        (3, 4): params["edge_cost_3_4"],
        (3, 5): params["edge_cost_3_5"],
        (3, 6): params["edge_cost_3_6"],
        (5, 6): params["edge_cost_5_6"],
    }

    def dcost(i, j):
        if i == j:
            return 0
        key = "deadhead_cost_{0}_{1}".format(min(i, j), max(i, j))
        return params[key]

    nodes = list(range(num_nodes))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    req_pairs = list(required_edges)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(req_pairs, domain=pyo.NonNegativeIntegers)
    model.yr = pyo.Var(req_pairs, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        expr = sum(dcost(i, j) * m.x[i, j] for (i, j) in arcs)
        expr += sum(service_cost[e] * (m.y[e] + m.yr[e]) for e in req_pairs)
        return expr
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def flow_rule(m, n):
        out_flow = sum(m.x[n, j] for j in nodes if j != n)
        in_flow = sum(m.x[i, n] for i in nodes if i != n)
        svc_out = sum(m.y[e] for e in req_pairs if e[0] == n)
        svc_out += sum(m.yr[e] for e in req_pairs if e[1] == n)
        svc_in = sum(m.y[e] for e in req_pairs if e[1] == n)
        svc_in += sum(m.yr[e] for e in req_pairs if e[0] == n)
        return (out_flow + svc_out) - (in_flow + svc_in) == 0
    model.flow = pyo.Constraint(nodes, rule=flow_rule)

    def svc_rule(m, e):
        return m.y[e] + m.yr[e] >= 1
    model.svc = pyo.Constraint(req_pairs, rule=svc_rule)

    def garage_rule(m):
        return sum(m.x[garage_node, j] for j in nodes if j != garage_node) + \
               sum(m.y[e] for e in req_pairs if e[0] == garage_node) + \
               sum(m.yr[e] for e in req_pairs if e[1] == garage_node) >= 1
    model.garage = pyo.Constraint(rule=garage_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
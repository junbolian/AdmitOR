import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = int(params["num_intersections"])
    num_req = int(params["num_required_segments"])
    dist = params["distance_matrix"]
    req = params["required_segment_relations"]

    nodes = list(range(N))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    req_list = [(int(a), int(b)) for a, b in req]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(dist[i][j] * m.flow[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, k):
        return (sum(m.flow[k, j] for j in nodes if j != k)
                - sum(m.flow[i, k] for i in nodes if i != k)) == 0
    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def req_rule(m, idx):
        a, b = req_list[idx]
        return m.flow[a, b] + m.flow[b, a] >= 1
    model.required = pyo.Constraint(range(num_req), rule=req_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_junctions = params["num_junctions"]
    num_required_segments = params["num_required_segments"]
    depot_junction = params["depot_junction"]
    required_segments = [tuple(seg) for seg in params["required_segments"]]

    nodes = list(range(num_junctions))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(distance_matrix[i][j] * m.x[i, j] for (i, j) in m.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def flow_balance_rule(m, j):
        inflow = sum(m.x[i, j] for i in m.nodes if i != j)
        outflow = sum(m.x[j, k] for k in m.nodes if k != j)
        return inflow - outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def depot_rule(m):
        outflow = sum(m.x[depot_junction, k] for k in m.nodes if k != depot_junction)
        return outflow >= 1

    model.depot_con = pyo.Constraint(rule=depot_rule)

    req_arcs = []
    for (a, b) in required_segments:
        req_arcs.append((a, b))
        if (b, a) not in req_arcs:
            req_arcs.append((b, a))

    model.req_set = pyo.Set(initialize=req_arcs, dimen=2, ordered=True)

    def service_rule(m, a, b):
        return m.x[a, b] + m.x[b, a] >= 1

    model.service = pyo.Constraint(model.req_set, rule=service_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
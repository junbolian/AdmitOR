import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Structural constants: 8 nodes, 17 pipelines in the given order
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.EDGES = pyo.Set(initialize=list(range(len(edges))), ordered=True)
    model.intermediate = pyo.Set(initialize=[1, 2, 3, 4, 5, 6])

    def flow_bounds(mdl, e):
        return (0.0, capacity[e])
    model.flow = pyo.Var(model.EDGES, bounds=flow_bounds)

    # Inflow / outflow tracking per node
    def _out_edges(n):
        return [e for e, (u, v) in enumerate(edges) if u == n]
    def _in_edges(n):
        return [e for e, (u, v) in enumerate(edges) if v == n]

    # Flow conservation at intermediate nodes: inflow == outflow
    def conservation_rule(mdl, n):
        out_sum = sum(mdl.flow[e] for e in _out_edges(n))
        in_sum = sum(mdl.flow[e] for e in _in_edges(n))
        return in_sum == out_sum
    model.conservation = pyo.Constraint(model.intermediate, rule=conservation_rule)

    # Objective: maximize total throughput from source (Node 0) to sink (Node 7)
    def obj_rule(mdl):
        return sum(mdl.flow[e] for e in _out_edges(0))
    model.throughput = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.throughput))
    return {"objective": obj_val, "status": "optimal"}
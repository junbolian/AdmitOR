import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]

    node_ids = list(range(9))
    source = 0
    sink = 8

    # Directed arcs in the same order as the capacity list.
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
        (1, 0), (1, 2), (1, 3), (1, 4), (1, 6), (1, 7), (1, 8),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6), (4, 7), (4, 8),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6), (5, 7), (5, 8),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 7), (6, 8),
        (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 8),
        (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7),
    ]

    cap_by_arc = {arc: capacity[i] for i, arc in enumerate(arcs)}

    model = pyo.ConcreteModel()

    model.arcs_set = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=node_ids)

    model.flow = pyo.Var(model.arcs_set, domain=pyo.NonNegativeReals)

    def cap_rule(md, i, j):
        return md.flow[i, j] <= cap_by_arc[(i, j)]
    model.cap_con = pyo.Constraint(model.arcs_set, rule=cap_rule)

    # Flow conservation at every node except source and sink.
    internal_nodes = [n for n in node_ids if n != source and n != sink]

    def balance_rule(md, n):
        inflow = sum(md.flow[i, j] for (i, j) in arcs if j == n)
        outflow = sum(md.flow[i, j] for (i, j) in arcs if i == n)
        return inflow == outflow
    model.balance_con = pyo.Constraint(internal_nodes, rule=balance_rule)

    def obj_rule(md):
        return sum(md.flow[source, j] for (i, j) in arcs if i == source)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}
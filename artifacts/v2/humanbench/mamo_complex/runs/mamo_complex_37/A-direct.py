import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]

    n = 8
    source = 0
    sink = 7

    # Ordered lexicographic list of (i, j) with i != j
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    cap = {arc: capacities[k] for k, arc in enumerate(arcs)}

    model = pyo.ConcreteModel()
    model.n = n
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def flow_ub_rule(model, i, j):
        return model.flow[(i, j)] <= cap[(i, j)]

    model.flow_ub = pyo.Constraint(model.arcs, rule=flow_ub_rule)

    nodes = range(n)

    def conservation_rule(model, k):
        inflow = sum(model.flow[(i, k)] for i in nodes if i != k)
        outflow = sum(model.flow[(k, j)] for j in nodes if j != k)
        if k == source:
            return outflow - inflow >= 0
        if k == sink:
            return inflow - outflow >= 0
        return inflow - outflow == 0

    model.conservation = pyo.Constraint(nodes, rule=conservation_rule)

    # Maximize net outflow from source
    model.obj = pyo.Objective(
        expr=sum(model.flow[(source, j)] for j in nodes if j != source)
        - sum(model.flow[(i, source)] for i in nodes if i != source),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
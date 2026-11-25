import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = [int(params["bandwidth_demand"][i]) for i in range(8)]
    edges = [(0, 1), (2, 4), (2, 7), (3, 7), (1, 4),
             (2, 3), (0, 5), (2, 5), (3, 5)]

    nodes = list(range(8))
    total = sum(demand)

    model = pyo.ConcreteModel()

    # start position of each node's contiguous spectrum block
    model.x = pyo.Var(nodes, domain=pyo.NonNegativeIntegers)

    # maximum utilized slot index across all nodes
    model.M = pyo.Var(domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=model.M, sense=pyo.minimize)

    # clash constraints: linked nodes must not overlap.
    # enforce an ordering (a before b or b before a) with big-M binaries
    M_big = total
    model.z = pyo.Var(edges, domain=pyo.Binary)
    model.clash = pyo.ConstraintList()
    for a, b in edges:
        model.clash.add(
            model.x[a] + demand[a] <= model.x[b] + M_big * (1 - model.z[a, b]))
        model.clash.add(
            model.x[b] + demand[b] <= model.x[a] + M_big * model.z[a, b])

    # span tracking and bounded horizon
    model.fit = pyo.ConstraintList()
    for i in nodes:
        model.fit.add(model.x[i] + demand[i] - 1 <= total - 1)
        model.fit.add(model.M >= model.x[i] + demand[i] - 1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
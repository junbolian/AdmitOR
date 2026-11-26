import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Cities / nodes
    nodes = [0, 1, 2, 3, 4, 5, 6]

    # Directed arcs with a given capacity in params
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 6),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    ]

    def cap(i, j):
        return params["capacity_{}_{}".format(i, j)]

    source = 0
    sink = 6

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    # Flow variables with arc capacities
    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap(i, j)

    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    # Flow conservation at each node
    def balance_rule(mdl, n):
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        if n == source:
            return outflow - inflow >= 0
        elif n == sink:
            return inflow - outflow >= 0
        else:
            return outflow - inflow == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    # Maximize net flow out of source into the sink
    model.obj = pyo.Objective(
        expr=sum(model.flow[i, j] for (i, j) in arcs if i == source)
        - sum(model.flow[i, j] for (i, j) in arcs if j == source),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
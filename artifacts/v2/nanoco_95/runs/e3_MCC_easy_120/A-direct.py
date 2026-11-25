import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coordinates"]
    lb = params["lower_bounds"]
    ub = params["upper_bounds"]
    cost = params["costs"]

    edges = [
        (0, 1), (0, 3), (0, 6), (1, 0), (1, 2), (1, 3),
        (1, 6), (2, 1), (2, 3), (3, 2), (3, 4), (4, 2),
        (4, 3), (4, 5), (5, 4), (5, 6), (6, 0), (6, 5),
    ]
    n_edges = len(edges)
    nodes = sorted({i for e in edges for i in e})

    model = pyo.ConcreteModel()

    model.E = pyo.RangeSet(0, n_edges - 1)
    model.V = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.E, bounds=lambda m, e: (lb[e], ub[e]))

    model.cost = pyo.Objective(
        expr=sum(cost[e] * model.flow[e] for e in model.E),
        sense=pyo.minimize,
    )

    out_edges = {v: [e for e in range(n_edges) if edges[e][0] == v] for v in nodes}
    in_edges = {v: [e for e in range(n_edges) if edges[e][1] == v] for v in nodes}

    def balance_rule(m, v):
        return (
            sum(m.flow[e] for e in in_edges[v])
            - sum(m.flow[e] for e in out_edges[v])
            == 0
        )

    model.balance = pyo.Constraint(model.V, rule=balance_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

ARCS = [
    (0, 1), (1, 2), (1, 4), (1, 5), (1, 7), (2, 3), (3, 4), (4, 5),
    (4, 8), (4, 9), (5, 6), (5, 7), (6, 7), (7, 8), (8, 9),
]
NODES = sorted({i for a in ARCS for i in a})
SOURCE = 0
SINK = 9


def solve(params):
    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=ARCS, dimen=2)

    cap = {a: params["capacity_%d_%d" % a] for a in ARCS}
    cst = {a: params["cost_%d_%d" % a] for a in ARCS}

    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals,
                      bounds=lambda mm, i, j: (0.0, cap[(i, j)]))

    def out_flow(mm, n):
        return sum(mm.f[i, j] for (i, j) in ARCS if i == n)

    def in_flow(mm, n):
        return sum(mm.f[i, j] for (i, j) in ARCS if j == n)

    model.cons = pyo.ConstraintList()
    for n in NODES:
        if n == SOURCE or n == SINK:
            continue
        model.cons.add(out_flow(model, n) - in_flow(model, n) == 0)

    model.flow_obj = pyo.Expression(expr=out_flow(model, SOURCE))
    model.cost_obj = pyo.Expression(
        expr=sum(cst[(i, j)] * model.f[i, j] for (i, j) in ARCS)
    )

    # ---- Stage 1: maximize total flow ----
    model.fo = pyo.Objective(expr=model.flow_obj, sense=pyo.maximize)
    Highs().solve(model)
    max_flow = pyo.value(model.flow_obj)

    # ---- Stage 2: fix max flow, minimize cost ----
    model.fo.deactivate()
    model.flow_fix = pyo.Constraint(expr=model.flow_obj == max_flow)

    model.co = pyo.Objective(expr=model.cost_obj, sense=pyo.minimize)
    Highs().solve(model)

    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}
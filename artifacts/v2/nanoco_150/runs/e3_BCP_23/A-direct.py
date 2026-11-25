import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (0, 3, params["weight_0_3"]),
        (1, 5, params["weight_1_5"]),
        (2, 4, params["weight_2_4"]),
        (3, 4, params["weight_3_4"]),
    ]

    model = pyo.ConcreteModel()
    model.platforms = pyo.Set(initialize=list(range(6)))
    model.edges = pyo.Set(initialize=[(u, v) for (u, v, _) in edges], dimen=2)

    model.x = pyo.Var(model.platforms, within=pyo.NonNegativeIntegers)
    model.z = pyo.Var(within=pyo.NonNegativeReals)

    # Objective span upper bound
    model.z_def = pyo.Constraint(
        model.platforms, rule=lambda mm, i: mm.z >= mm.x[i]
    )

    # Binary selector: y=1 -> x[v] - x[u] >= d ; y=0 -> x[u] - x[v] >= d
    model.y = pyo.Var(model.edges, within=pyo.Binary)

    weight_map = {(u, v): w for (u, v, w) in edges}
    big_m = 6  # safe upper bound on any index difference

    def sep_rule(mm, u, v):
        d = weight_map[(u, v)]
        return mm.x[v] - mm.x[u] >= d - big_m * (1 - mm.y[u, v])

    def sep_rule_rev(mm, u, v):
        d = weight_map[(u, v)]
        return mm.x[u] - mm.x[v] >= d - big_m * mm.y[u, v]

    model.sep_fwd = pyo.Constraint(model.edges, rule=sep_rule)
    model.sep_rev = pyo.Constraint(model.edges, rule=sep_rule_rev)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
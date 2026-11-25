import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pair_weights = params["pair_weights"]
    facilities_to_select = params["facilities_to_select"]

    locations = [0, 1, 2, 3]
    pairs = [
        (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 3),
        (3, 0), (3, 1), (3, 2),
    ]

    weight = {}
    for idx, pr in enumerate(pairs):
        weight[pr] = float(pair_weights[idx])

    model = pyo.ConcreteModel()

    model.LOC = pyo.Set(initialize=locations)
    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    model.y = pyo.Var(model.LOC, domain=pyo.Binary)
    model.z = pyo.Var(model.PAIRS, domain=pyo.Binary)

    model.select_count = pyo.Constraint(
        expr=sum(model.y[i] for i in model.LOC) == facilities_to_select
    )

    def pair_ub_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.y[i]

    def pair_ub2_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.y[j]

    def pair_lb_rule(mdl, i, j):
        return mdl.z[i, j] >= mdl.y[i] + mdl.y[j] - 1

    model.pair_ub = pyo.Constraint(model.PAIRS, rule=pair_ub_rule)
    model.pair_ub2 = pyo.Constraint(model.PAIRS, rule=pair_ub2_rule)
    model.pair_lb = pyo.Constraint(model.PAIRS, rule=pair_lb_rule)

    model.total_dispersion = pyo.Objective(
        expr=sum(weight[(i, j)] * model.z[i, j] for (i, j) in model.PAIRS),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_dispersion))
    return {"objective": obj_val, "status": "optimal"}
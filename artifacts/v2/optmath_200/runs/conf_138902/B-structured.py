# IR: {"sets":{"I":[0,1,2,3,4,5],"B":[0,1,2,3,4,5]},"params":{"capacity":"params['bin_capacity']","weight[i]":"params['item_weights'][i]"},"variables":{"x[i,b]":"binary assignment","y[b]":"binary bin usage"},"constraints":["For each i in I: sum_b x[i,b] = 1","For each b in B: sum_i weight[i]*x[i,b] <= capacity*y[b]","For each i in I,b in B: x[i,b] <= y[b]","For each b in B: y[b] <= sum_i x[i,b]"],"objective":"minimize sum_b y[b]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 5)
    model.B = pyo.RangeSet(0, 5)

    model.capacity = pyo.Param(initialize=params["bin_capacity"])
    model.weight = pyo.Param(
        model.I,
        initialize={i: params["item_weights"][i] for i in model.I},
    )

    model.x = pyo.Var(model.I, model.B, domain=pyo.Binary)
    model.y = pyo.Var(model.B, domain=pyo.Binary)

    def assignment_rule(mod, i):
        return sum(mod.x[i, b] for b in mod.B) == 1

    model.item_assignment = pyo.Constraint(model.I, rule=assignment_rule)

    def capacity_rule(mod, b):
        return (
            sum(mod.weight[i] * mod.x[i, b] for i in mod.I)
            <= mod.capacity * mod.y[b]
        )

    model.capacity_limit = pyo.Constraint(model.B, rule=capacity_rule)

    def assignment_usage_rule(mod, i, b):
        return mod.x[i, b] <= mod.y[b]

    model.assignment_usage = pyo.Constraint(
        model.I, model.B, rule=assignment_usage_rule
    )

    def nonempty_usage_rule(mod, b):
        return mod.y[b] <= sum(mod.x[i, b] for i in mod.I)

    model.nonempty_usage = pyo.Constraint(model.B, rule=nonempty_usage_rule)

    model.total_bins = pyo.Objective(
        expr=sum(model.y[b] for b in model.B),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_bins))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
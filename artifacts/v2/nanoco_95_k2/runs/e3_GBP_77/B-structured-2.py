# IR: {"sets":{"I":[0,1,2,3],"S":[0,1,2,3],"P":"{(i,j): i,j in I, i<j}","D":["left","right","below","above"]},"params":{"W":"params['sheet_width']","H":"params['sheet_height']","w[i]":"params['part_widths'][i]","h[i]":"params['part_heights'][i]"},"variables":{"used[s]":"binary","assigned[i,s]":"binary","x[i]":"continuous nonnegative","y[i]":"continuous nonnegative","separated[i,j,s,d]":"binary"},"constraints":["sum(s in S, assigned[i,s]) = 1 for i in I","assigned[i,s] <= used[s] for i in I,s in S","x[i] + w[i] <= W for i in I","y[i] + h[i] <= H for i in I","sum(d in D, separated[i,j,s,d]) >= assigned[i,s] + assigned[j,s] - 1 for (i,j) in P,s in S","x[i] + w[i] <= x[j] + W*(1-separated[i,j,s,'left']) for (i,j) in P,s in S","x[j] + w[j] <= x[i] + W*(1-separated[i,j,s,'right']) for (i,j) in P,s in S","y[i] + h[i] <= y[j] + H*(1-separated[i,j,s,'below']) for (i,j) in P,s in S","y[j] + h[j] <= y[i] + H*(1-separated[i,j,s,'above']) for (i,j) in P,s in S"],"objective":"minimize sum(s in S, used[s])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sheet_width = params["sheet_width"]
    sheet_height = params["sheet_height"]
    part_widths = params["part_widths"]
    part_heights = params["part_heights"]

    if len(part_widths) != 4 or len(part_heights) != 4:
        raise ValueError("Exactly four part widths and heights are required.")

    model = pyo.ConcreteModel()

    # Four candidate sheets suffice: every feasible part can use its own sheet.
    model.I = pyo.RangeSet(0, 3)
    model.S = pyo.RangeSet(0, 3)
    model.P = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(4) for j in range(i + 1, 4)],
    )
    model.D = pyo.Set(
        initialize=["left", "right", "below", "above"],
        ordered=True,
    )

    model.W = pyo.Param(initialize=sheet_width, within=pyo.PositiveReals)
    model.H = pyo.Param(initialize=sheet_height, within=pyo.PositiveReals)
    model.w = pyo.Param(
        model.I,
        initialize={i: part_widths[i] for i in range(4)},
        within=pyo.PositiveReals,
    )
    model.h = pyo.Param(
        model.I,
        initialize={i: part_heights[i] for i in range(4)},
        within=pyo.PositiveReals,
    )

    model.used = pyo.Var(model.S, domain=pyo.Binary)
    model.assigned = pyo.Var(model.I, model.S, domain=pyo.Binary)
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.separated = pyo.Var(
        model.P, model.S, model.D, domain=pyo.Binary
    )

    def assignment_rule(b, i):
        return sum(b.assigned[i, s] for s in b.S) == 1

    model.assign_once = pyo.Constraint(model.I, rule=assignment_rule)

    def usage_rule(b, i, s):
        return b.assigned[i, s] <= b.used[s]

    model.link_usage = pyo.Constraint(model.I, model.S, rule=usage_rule)

    def width_rule(b, i):
        return b.x[i] + b.w[i] <= b.W

    model.width_boundary = pyo.Constraint(model.I, rule=width_rule)

    def height_rule(b, i):
        return b.y[i] + b.h[i] <= b.H

    model.height_boundary = pyo.Constraint(model.I, rule=height_rule)

    def separation_required_rule(b, i, j, s):
        return (
            sum(b.separated[i, j, s, d] for d in b.D)
            >= b.assigned[i, s] + b.assigned[j, s] - 1
        )

    model.require_separation = pyo.Constraint(
        model.P, model.S, rule=separation_required_rule
    )

    # Sheet dimensions are valid big-M values because all parts are bounded
    # within a sheet and their lower-left coordinates are nonnegative.
    def left_rule(b, i, j, s):
        return (
            b.x[i] + b.w[i]
            <= b.x[j] + b.W * (1 - b.separated[i, j, s, "left"])
        )

    model.left_separation = pyo.Constraint(
        model.P, model.S, rule=left_rule
    )

    def right_rule(b, i, j, s):
        return (
            b.x[j] + b.w[j]
            <= b.x[i] + b.W * (1 - b.separated[i, j, s, "right"])
        )

    model.right_separation = pyo.Constraint(
        model.P, model.S, rule=right_rule
    )

    def below_rule(b, i, j, s):
        return (
            b.y[i] + b.h[i]
            <= b.y[j] + b.H * (1 - b.separated[i, j, s, "below"])
        )

    model.below_separation = pyo.Constraint(
        model.P, model.S, rule=below_rule
    )

    def above_rule(b, i, j, s):
        return (
            b.y[j] + b.h[j]
            <= b.y[i] + b.H * (1 - b.separated[i, j, s, "above"])
        )

    model.above_separation = pyo.Constraint(
        model.P, model.S, rule=above_rule
    )

    model.total_sheets = pyo.Objective(
        expr=sum(model.used[s] for s in model.S),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_sheets))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"P":[0,1,2,3],"B":[0,1,2,3],"Q":"{(i,j) in P x P: i<j}","D":[0,1,2,3]},"params":{"hide_width":"params['hide_width']","hide_height":"params['hide_height']","patch_widths":"params['patch_widths'], indexed by P","patch_heights":"params['patch_heights'], indexed by P"},"variables":{"assigned[i,b]":"binary","used[b]":"binary","x[i]":"nonnegative continuous","y[i]":"nonnegative continuous","separate[i,j,b,d]":"binary; directions left,right,below,above"},"constraints":["sum_b assigned[i,b] = 1 for i in P","assigned[i,b] <= used[b] for i in P,b in B","used[b] <= sum_i assigned[i,b] for b in B","x[i]+patch_widths[i] <= hide_width for i in P","y[i]+patch_heights[i] <= hide_height for i in P","sum_d separate[i,j,b,d] >= assigned[i,b]+assigned[j,b]-1 for (i,j) in Q,b in B","x[i]+patch_widths[i] <= x[j]+hide_width*(1-separate[i,j,b,0]) for (i,j) in Q,b in B","x[j]+patch_widths[j] <= x[i]+hide_width*(1-separate[i,j,b,1]) for (i,j) in Q,b in B","y[i]+patch_heights[i] <= y[j]+hide_height*(1-separate[i,j,b,2]) for (i,j) in Q,b in B","y[j]+patch_heights[j] <= y[i]+hide_height*(1-separate[i,j,b,3]) for (i,j) in Q,b in B"],"objective":"minimize sum_b used[b]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Four candidate hides suffice: each patch can use its own hide.
    model.P = pyo.RangeSet(0, 3)
    model.B = pyo.RangeSet(0, 3)
    model.Q = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(4) for j in range(i + 1, 4)],
    )
    model.D = pyo.RangeSet(0, 3)

    model.hide_width = pyo.Param(
        initialize=float(params["hide_width"]),
        within=pyo.PositiveReals,
    )
    model.hide_height = pyo.Param(
        initialize=float(params["hide_height"]),
        within=pyo.PositiveReals,
    )
    model.patch_widths = pyo.Param(
        model.P,
        initialize={i: float(params["patch_widths"][i]) for i in model.P},
        within=pyo.PositiveReals,
    )
    model.patch_heights = pyo.Param(
        model.P,
        initialize={i: float(params["patch_heights"][i]) for i in model.P},
        within=pyo.PositiveReals,
    )

    model.assigned = pyo.Var(model.P, model.B, domain=pyo.Binary)
    model.used = pyo.Var(model.B, domain=pyo.Binary)
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.separate = pyo.Var(model.Q, model.B, model.D, domain=pyo.Binary)

    model.single_hide = pyo.Constraint(
        model.P,
        rule=lambda mdl, i: sum(mdl.assigned[i, b] for b in mdl.B) == 1,
    )

    model.assignment_requires_hide = pyo.Constraint(
        model.P,
        model.B,
        rule=lambda mdl, i, b: mdl.assigned[i, b] <= mdl.used[b],
    )

    model.used_hide_has_patch = pyo.Constraint(
        model.B,
        rule=lambda mdl, b: mdl.used[b]
        <= sum(mdl.assigned[i, b] for i in mdl.P),
    )

    model.horizontal_containment = pyo.Constraint(
        model.P,
        rule=lambda mdl, i: mdl.x[i] + mdl.patch_widths[i] <= mdl.hide_width,
    )

    model.vertical_containment = pyo.Constraint(
        model.P,
        rule=lambda mdl, i: mdl.y[i] + mdl.patch_heights[i] <= mdl.hide_height,
    )

    model.require_separation = pyo.Constraint(
        model.Q,
        model.B,
        rule=lambda mdl, i, j, b: sum(
            mdl.separate[i, j, b, d] for d in mdl.D
        )
        >= mdl.assigned[i, b] + mdl.assigned[j, b] - 1,
    )

    # Containment makes the hide dimensions valid big-M constants.
    model.separation_left = pyo.Constraint(
        model.Q,
        model.B,
        rule=lambda mdl, i, j, b: mdl.x[i] + mdl.patch_widths[i]
        <= mdl.x[j] + mdl.hide_width * (1 - mdl.separate[i, j, b, 0]),
    )

    model.separation_right = pyo.Constraint(
        model.Q,
        model.B,
        rule=lambda mdl, i, j, b: mdl.x[j] + mdl.patch_widths[j]
        <= mdl.x[i] + mdl.hide_width * (1 - mdl.separate[i, j, b, 1]),
    )

    model.separation_below = pyo.Constraint(
        model.Q,
        model.B,
        rule=lambda mdl, i, j, b: mdl.y[i] + mdl.patch_heights[i]
        <= mdl.y[j] + mdl.hide_height * (1 - mdl.separate[i, j, b, 2]),
    )

    model.separation_above = pyo.Constraint(
        model.Q,
        model.B,
        rule=lambda mdl, i, j, b: mdl.y[j] + mdl.patch_heights[j]
        <= mdl.y[i] + mdl.hide_height * (1 - mdl.separate[i, j, b, 3]),
    )

    model.total_hides = pyo.Objective(
        expr=sum(model.used[b] for b in model.B),
        sense=pyo.minimize,
    )

    # Appsi raises RuntimeError when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_hides))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
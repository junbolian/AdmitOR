# IR: {"sets":{"P":[0,1,2,3],"B":[0,1,2,3],"Q":"{(i,j): i,j in P, i<j}","D":["left","right","below","above"]},"params":{"W":"params['hide_width']","H":"params['hide_height']","w[i]":"params['patch_widths'][i]","h[i]":"params['patch_heights'][i]"},"variables":{"a[i,b]":"binary; patch-to-hide assignment","u[b]":"binary; hide used","x[i]":"nonnegative continuous","y[i]":"nonnegative continuous","s[i,j,d]":"binary; relative separation"},"constraints":["sum_b a[i,b] = 1 for each i","a[i,b] <= u[b] for each i,b","u[b] <= sum_i a[i,b] for each b","x[i]+w[i] <= W for each i","y[i]+h[i] <= H for each i","sum_d s[i,j,d] <= 1 for each (i,j)","sum_d s[i,j,d] >= a[i,b]+a[j,b]-1 for each (i,j),b","x[i]+w[i] <= x[j]+W*(1-s[i,j,left]) for each (i,j)","x[j]+w[j] <= x[i]+W*(1-s[i,j,right]) for each (i,j)","y[i]+h[i] <= y[j]+H*(1-s[i,j,below]) for each (i,j)","y[j]+h[j] <= y[i]+H*(1-s[i,j,above]) for each (i,j)"],"objective":"minimize sum_b u[b]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Four hides suffice whenever the instance is feasible: one per patch.
    model.P = pyo.Set(initialize=range(4), ordered=True)
    model.B = pyo.Set(initialize=range(4), ordered=True)
    model.Q = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(4) for j in range(i + 1, 4)],
    )
    model.D = pyo.Set(
        initialize=["left", "right", "below", "above"], ordered=True
    )

    model.W = pyo.Param(
        initialize=float(params["hide_width"]), within=pyo.PositiveReals
    )
    model.H = pyo.Param(
        initialize=float(params["hide_height"]), within=pyo.PositiveReals
    )
    model.w = pyo.Param(
        model.P,
        initialize={i: float(params["patch_widths"][i]) for i in model.P},
        within=pyo.PositiveReals,
    )
    model.h = pyo.Param(
        model.P,
        initialize={i: float(params["patch_heights"][i]) for i in model.P},
        within=pyo.PositiveReals,
    )

    model.a = pyo.Var(model.P, model.B, domain=pyo.Binary)
    model.u = pyo.Var(model.B, domain=pyo.Binary)
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.s = pyo.Var(model.Q, model.D, domain=pyo.Binary)

    model.assign_once = pyo.Constraint(
        model.P,
        rule=lambda md, i: sum(md.a[i, b] for b in md.B) == 1,
    )
    model.assignment_requires_hide = pyo.Constraint(
        model.P, model.B,
        rule=lambda md, i, b: md.a[i, b] <= md.u[b],
    )
    model.used_hide_has_patch = pyo.Constraint(
        model.B,
        rule=lambda md, b: md.u[b] <= sum(md.a[i, b] for i in md.P),
    )

    # Coordinates are local to the assigned hide; dimensions are never swapped.
    model.horizontal_containment = pyo.Constraint(
        model.P, rule=lambda md, i: md.x[i] + md.w[i] <= md.W
    )
    model.vertical_containment = pyo.Constraint(
        model.P, rule=lambda md, i: md.y[i] + md.h[i] <= md.H
    )

    model.at_most_one_separation = pyo.Constraint(
        model.Q,
        rule=lambda md, i, j: sum(md.s[i, j, d] for d in md.D) <= 1,
    )
    model.shared_hide_requires_separation = pyo.Constraint(
        model.Q, model.B,
        rule=lambda md, i, j, b: (
            sum(md.s[i, j, d] for d in md.D)
            >= md.a[i, b] + md.a[j, b] - 1
        ),
    )

    # Containment makes W and H valid big-M values.
    model.left_separation = pyo.Constraint(
        model.Q,
        rule=lambda md, i, j: (
            md.x[i] + md.w[i]
            <= md.x[j] + md.W * (1 - md.s[i, j, "left"])
        ),
    )
    model.right_separation = pyo.Constraint(
        model.Q,
        rule=lambda md, i, j: (
            md.x[j] + md.w[j]
            <= md.x[i] + md.W * (1 - md.s[i, j, "right"])
        ),
    )
    model.below_separation = pyo.Constraint(
        model.Q,
        rule=lambda md, i, j: (
            md.y[i] + md.h[i]
            <= md.y[j] + md.H * (1 - md.s[i, j, "below"])
        ),
    )
    model.above_separation = pyo.Constraint(
        model.Q,
        rule=lambda md, i, j: (
            md.y[j] + md.h[j]
            <= md.y[i] + md.H * (1 - md.s[i, j, "above"])
        ),
    )

    model.total_hides = pyo.Objective(
        expr=sum(model.u[b] for b in model.B),
        sense=pyo.minimize,
    )

    # APPsi raises RuntimeError if it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_hides))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
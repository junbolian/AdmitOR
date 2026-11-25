# IR: {"sets":{"I":[0,1,2,3],"H":[0,1,2,3],"P":"{(i,j): i,j in I, i<j}","D":["left","right","below","above"]},"params":{"W":"params['hide_width']","T":"params['hide_height']","w[i]":"params['patch_widths'][i]","t[i]":"params['patch_heights'][i]"},"variables":{"used[h]":"binary","assign[i,h]":"binary","x[i]":"continuous >= 0","y[i]":"continuous >= 0","sep[i,j,h,d]":"binary"},"constraints":["sum_h assign[i,h] = 1 for i in I","assign[i,h] <= used[h] for i in I,h in H","used[h] <= sum_i assign[i,h] for h in H","x[i]+w[i] <= W for i in I","y[i]+t[i] <= T for i in I","sum_d sep[i,j,h,d] >= assign[i,h]+assign[j,h]-1 for (i,j) in P,h in H","sum_d sep[i,j,h,d] <= assign[i,h] for (i,j) in P,h in H","sum_d sep[i,j,h,d] <= assign[j,h] for (i,j) in P,h in H","x[i]+w[i] <= x[j]+W*(1-sep[i,j,h,'left']) for (i,j) in P,h in H","x[j]+w[j] <= x[i]+W*(1-sep[i,j,h,'right']) for (i,j) in P,h in H","y[i]+t[i] <= y[j]+T*(1-sep[i,j,h,'below']) for (i,j) in P,h in H","y[j]+t[j] <= y[i]+T*(1-sep[i,j,h,'above']) for (i,j) in P,h in H","used[h] >= used[h+1] for h in {0,1,2}"],"objective":"minimize sum_h used[h]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Four hides suffice whenever all four patches individually fit.
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 3)
    model.H = pyo.RangeSet(0, 3)
    model.P = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(4) for j in range(i + 1, 4)],
    )
    model.D = pyo.Set(initialize=["left", "right", "below", "above"])

    model.W = pyo.Param(
        initialize=params["hide_width"], within=pyo.PositiveReals
    )
    model.T = pyo.Param(
        initialize=params["hide_height"], within=pyo.PositiveReals
    )
    model.w = pyo.Param(
        model.I,
        initialize={i: params["patch_widths"][i] for i in range(4)},
        within=pyo.PositiveReals,
    )
    model.t = pyo.Param(
        model.I,
        initialize={i: params["patch_heights"][i] for i in range(4)},
        within=pyo.PositiveReals,
    )

    model.used = pyo.Var(model.H, domain=pyo.Binary)
    model.assign = pyo.Var(model.I, model.H, domain=pyo.Binary)
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.sep = pyo.Var(model.P, model.H, model.D, domain=pyo.Binary)

    model.single_hide = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: sum(mdl.assign[i, h] for h in mdl.H) == 1,
    )
    model.assignment_requires_hide = pyo.Constraint(
        model.I,
        model.H,
        rule=lambda mdl, i, h: mdl.assign[i, h] <= mdl.used[h],
    )
    model.hide_requires_assignment = pyo.Constraint(
        model.H,
        rule=lambda mdl, h: mdl.used[h]
        <= sum(mdl.assign[i, h] for i in mdl.I),
    )

    # Coordinates are lower-left corners; fixed dimensions prohibit rotation.
    model.horizontal_containment = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: mdl.x[i] + mdl.w[i] <= mdl.W,
    )
    model.vertical_containment = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: mdl.y[i] + mdl.t[i] <= mdl.T,
    )

    model.require_separation = pyo.Constraint(
        model.P,
        model.H,
        rule=lambda mdl, i, j, h: sum(
            mdl.sep[i, j, h, direction] for direction in mdl.D
        )
        >= mdl.assign[i, h] + mdl.assign[j, h] - 1,
    )
    model.separation_requires_first = pyo.Constraint(
        model.P,
        model.H,
        rule=lambda mdl, i, j, h: sum(
            mdl.sep[i, j, h, direction] for direction in mdl.D
        )
        <= mdl.assign[i, h],
    )
    model.separation_requires_second = pyo.Constraint(
        model.P,
        model.H,
        rule=lambda mdl, i, j, h: sum(
            mdl.sep[i, j, h, direction] for direction in mdl.D
        )
        <= mdl.assign[j, h],
    )

    # Containment makes the hide dimensions valid big-M coefficients.
    model.left_separation = pyo.Constraint(
        model.P,
        model.H,
        rule=lambda mdl, i, j, h: mdl.x[i] + mdl.w[i]
        <= mdl.x[j] + mdl.W * (1 - mdl.sep[i, j, h, "left"]),
    )
    model.right_separation = pyo.Constraint(
        model.P,
        model.H,
        rule=lambda mdl, i, j, h: mdl.x[j] + mdl.w[j]
        <= mdl.x[i] + mdl.W * (1 - mdl.sep[i, j, h, "right"]),
    )
    model.below_separation = pyo.Constraint(
        model.P,
        model.H,
        rule=lambda mdl, i, j, h: mdl.y[i] + mdl.t[i]
        <= mdl.y[j] + mdl.T * (1 - mdl.sep[i, j, h, "below"]),
    )
    model.above_separation = pyo.Constraint(
        model.P,
        model.H,
        rule=lambda mdl, i, j, h: mdl.y[j] + mdl.t[j]
        <= mdl.y[i] + mdl.T * (1 - mdl.sep[i, j, h, "above"]),
    )

    model.hide_order = pyo.Constraint(
        range(3),
        rule=lambda mdl, h: mdl.used[h] >= mdl.used[h + 1],
    )

    model.total_hides = pyo.Objective(
        expr=sum(model.used[h] for h in model.H),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver/runtime errors must propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Objective retrieval alone determines success.
    try:
        obj_val = float(pyo.value(model.total_hides))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"I":[1,2,3,4,5],"K":[1,2,3,4,5],"P":"{(i,j): i,j in I, i<j}","D":["left","right","below","above"]},"params":{"wafer_width":"params['wafer_width']","wafer_height":"params['wafer_height']","ic1_width":"params['ic1_width']","ic1_height":"params['ic1_height']","ic2_width":"params['ic2_width']","ic2_height":"params['ic2_height']","ic3_width":"params['ic3_width']","ic3_height":"params['ic3_height']","ic4_width":"params['ic4_width']","ic4_height":"params['ic4_height']","ic5_width":"params['ic5_width']","ic5_height":"params['ic5_height']"},"derived":{"W":"wafer_width","H":"wafer_height","w[i]":"ic{i}_width","h[i]":"ic{i}_height"},"variables":{"x[i]":"continuous >= 0","y[i]":"continuous >= 0","assigned[i,k]":"binary","used[k]":"binary","separation[i,j,k,d]":"binary"},"constraints":["sum(k in K, assigned[i,k]) = 1 for i in I","assigned[i,k] <= used[k] for i in I,k in K","used[k] <= sum(i in I, assigned[i,k]) for k in K","x[i]+w[i] <= W for i in I","y[i]+h[i] <= H for i in I","sum(d in D,separation[i,j,k,d]) >= assigned[i,k]+assigned[j,k]-1 for (i,j) in P,k in K","sum(d in D,separation[i,j,k,d]) <= assigned[i,k] for (i,j) in P,k in K","sum(d in D,separation[i,j,k,d]) <= assigned[j,k] for (i,j) in P,k in K","x[i]+w[i] <= x[j]+W*(1-separation[i,j,k,'left']) for (i,j) in P,k in K","x[j]+w[j] <= x[i]+W*(1-separation[i,j,k,'right']) for (i,j) in P,k in K","y[i]+h[i] <= y[j]+H*(1-separation[i,j,k,'below']) for (i,j) in P,k in K","y[j]+h[j] <= y[i]+H*(1-separation[i,j,k,'above']) for (i,j) in P,k in K"],"objective":"minimize sum(k in K,used[k])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Five wafers suffice: every circuit can occupy its own wafer.
    model.I = pyo.RangeSet(1, 5)
    model.K = pyo.RangeSet(1, 5)
    model.P = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 6)
            for j in range(i + 1, 6)
        ],
    )
    model.D = pyo.Set(initialize=["left", "right", "below", "above"])

    model.W = pyo.Param(initialize=params["wafer_width"])
    model.H = pyo.Param(initialize=params["wafer_height"])
    model.w = pyo.Param(
        model.I,
        initialize={
            1: params["ic1_width"],
            2: params["ic2_width"],
            3: params["ic3_width"],
            4: params["ic4_width"],
            5: params["ic5_width"],
        },
    )
    model.h = pyo.Param(
        model.I,
        initialize={
            1: params["ic1_height"],
            2: params["ic2_height"],
            3: params["ic3_height"],
            4: params["ic4_height"],
            5: params["ic5_height"],
        },
    )

    # Coordinates refer to each circuit's lower-left corner on its wafer.
    # Widths and heights are fixed; there are no rotation variables.
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.assigned = pyo.Var(model.I, model.K, domain=pyo.Binary)
    model.used = pyo.Var(model.K, domain=pyo.Binary)
    model.separation = pyo.Var(
        model.P, model.K, model.D, domain=pyo.Binary
    )

    model.assign_once = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: sum(
            mdl.assigned[i, k] for k in mdl.K
        ) == 1,
    )

    model.assignment_requires_wafer = pyo.Constraint(
        model.I,
        model.K,
        rule=lambda mdl, i, k: mdl.assigned[i, k] <= mdl.used[k],
    )

    model.used_wafer_has_circuit = pyo.Constraint(
        model.K,
        rule=lambda mdl, k: mdl.used[k] <= sum(
            mdl.assigned[i, k] for i in mdl.I
        ),
    )

    model.horizontal_boundary = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: mdl.x[i] + mdl.w[i] <= mdl.W,
    )

    model.vertical_boundary = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: mdl.y[i] + mdl.h[i] <= mdl.H,
    )

    def separation_required_rule(mdl, i, j, k):
        return sum(
            mdl.separation[i, j, k, direction] for direction in mdl.D
        ) >= mdl.assigned[i, k] + mdl.assigned[j, k] - 1

    model.separation_required = pyo.Constraint(
        model.P, model.K, rule=separation_required_rule
    )

    def separation_first_assignment_rule(mdl, i, j, k):
        return sum(
            mdl.separation[i, j, k, direction] for direction in mdl.D
        ) <= mdl.assigned[i, k]

    model.separation_first_assignment = pyo.Constraint(
        model.P, model.K, rule=separation_first_assignment_rule
    )

    def separation_second_assignment_rule(mdl, i, j, k):
        return sum(
            mdl.separation[i, j, k, direction] for direction in mdl.D
        ) <= mdl.assigned[j, k]

    model.separation_second_assignment = pyo.Constraint(
        model.P, model.K, rule=separation_second_assignment_rule
    )

    # Wafer dimensions are valid big-M values because of the boundaries.
    model.left_separation = pyo.Constraint(
        model.P,
        model.K,
        rule=lambda mdl, i, j, k: (
            mdl.x[i] + mdl.w[i]
            <= mdl.x[j] + mdl.W * (1 - mdl.separation[i, j, k, "left"])
        ),
    )

    model.right_separation = pyo.Constraint(
        model.P,
        model.K,
        rule=lambda mdl, i, j, k: (
            mdl.x[j] + mdl.w[j]
            <= mdl.x[i] + mdl.W * (1 - mdl.separation[i, j, k, "right"])
        ),
    )

    model.below_separation = pyo.Constraint(
        model.P,
        model.K,
        rule=lambda mdl, i, j, k: (
            mdl.y[i] + mdl.h[i]
            <= mdl.y[j] + mdl.H * (1 - mdl.separation[i, j, k, "below"])
        ),
    )

    model.above_separation = pyo.Constraint(
        model.P,
        model.K,
        rule=lambda mdl, i, j, k: (
            mdl.y[j] + mdl.h[j]
            <= mdl.y[i] + mdl.H * (1 - mdl.separation[i, j, k, "above"])
        ),
    )

    model.total_wafers = pyo.Objective(
        expr=sum(model.used[k] for k in model.K),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    # Success is determined solely by objective-value retrieval.
    try:
        obj_val = float(pyo.value(model.total_wafers))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
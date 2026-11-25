# IR: {"sets":{"I":[0,1,2,3],"K":[0,1,2,3],"P":"{(i,j): i,j in I, i<j}","D":[0,1,2,3]},"params":{"W":"params['frame_width']","H":"params['frame_height']","w[i]":"params['array_widths'][i]","h[i]":"params['array_heights'][i]"},"variables":{"assigned[i,k]":"binary","used[k]":"binary","x[i]":"nonnegative continuous","y[i]":"nonnegative continuous","direction[i,j,d]":"binary"},"constraints":["sum_k assigned[i,k] = 1 for each i","assigned[i,k] <= used[k] for each i,k","used[k] <= sum_i assigned[i,k] for each k","x[i] + w[i] <= W for each i","y[i] + h[i] <= H for each i","sum_d direction[i,j,d] <= 1 for each (i,j)","sum_d direction[i,j,d] >= assigned[i,k] + assigned[j,k] - 1 for each (i,j),k","x[i] + w[i] <= x[j] + W*(1-direction[i,j,0]) for each (i,j)","x[j] + w[j] <= x[i] + W*(1-direction[i,j,1]) for each (i,j)","y[i] + h[i] <= y[j] + H*(1-direction[i,j,2]) for each (i,j)","y[j] + h[j] <= y[i] + H*(1-direction[i,j,3]) for each (i,j)","used[k] >= used[k+1] for k=0,1,2"],"objective":"minimize sum_k used[k]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Four frames suffice whenever each individual array fits a frame.
    model.I = pyo.RangeSet(0, 3)
    model.K = pyo.RangeSet(0, 3)
    model.P = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(4) for j in range(i + 1, 4)],
    )
    model.D = pyo.RangeSet(0, 3)

    model.W = pyo.Param(initialize=float(params["frame_width"]))
    model.H = pyo.Param(initialize=float(params["frame_height"]))
    model.w = pyo.Param(
        model.I,
        initialize={
            i: float(params["array_widths"][i]) for i in range(4)
        },
    )
    model.h = pyo.Param(
        model.I,
        initialize={
            i: float(params["array_heights"][i]) for i in range(4)
        },
    )

    model.assigned = pyo.Var(model.I, model.K, domain=pyo.Binary)
    model.used = pyo.Var(model.K, domain=pyo.Binary)
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.direction = pyo.Var(model.P, model.D, domain=pyo.Binary)

    model.single_assignment = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: sum(
            mdl.assigned[i, k] for k in mdl.K
        ) == 1,
    )

    model.assignment_requires_frame = pyo.Constraint(
        model.I,
        model.K,
        rule=lambda mdl, i, k: mdl.assigned[i, k] <= mdl.used[k],
    )

    model.used_frame_nonempty = pyo.Constraint(
        model.K,
        rule=lambda mdl, k: mdl.used[k] <= sum(
            mdl.assigned[i, k] for i in mdl.I
        ),
    )

    # Coordinates are measured from the lower-left corner of the assigned frame.
    # Fixed dimensions, with no orientation variables, prohibit rotation.
    model.horizontal_containment = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: mdl.x[i] + mdl.w[i] <= mdl.W,
    )

    model.vertical_containment = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: mdl.y[i] + mdl.h[i] <= mdl.H,
    )

    model.at_most_one_direction = pyo.Constraint(
        model.P,
        rule=lambda mdl, i, j: sum(
            mdl.direction[i, j, d] for d in mdl.D
        ) <= 1,
    )

    model.shared_frame_separation = pyo.Constraint(
        model.P,
        model.K,
        rule=lambda mdl, i, j, k: sum(
            mdl.direction[i, j, d] for d in mdl.D
        ) >= mdl.assigned[i, k] + mdl.assigned[j, k] - 1,
    )

    # Frame dimensions are valid big-M values because of containment.
    model.first_left_of_second = pyo.Constraint(
        model.P,
        rule=lambda mdl, i, j: (
            mdl.x[i] + mdl.w[i]
            <= mdl.x[j] + mdl.W * (1 - mdl.direction[i, j, 0])
        ),
    )

    model.second_left_of_first = pyo.Constraint(
        model.P,
        rule=lambda mdl, i, j: (
            mdl.x[j] + mdl.w[j]
            <= mdl.x[i] + mdl.W * (1 - mdl.direction[i, j, 1])
        ),
    )

    model.first_below_second = pyo.Constraint(
        model.P,
        rule=lambda mdl, i, j: (
            mdl.y[i] + mdl.h[i]
            <= mdl.y[j] + mdl.H * (1 - mdl.direction[i, j, 2])
        ),
    )

    model.second_below_first = pyo.Constraint(
        model.P,
        rule=lambda mdl, i, j: (
            mdl.y[j] + mdl.h[j]
            <= mdl.y[i] + mdl.H * (1 - mdl.direction[i, j, 3])
        ),
    )

    model.frame_symmetry = pyo.Constraint(
        range(3),
        rule=lambda mdl, k: mdl.used[k] >= mdl.used[k + 1],
    )

    model.total_frames = pyo.Objective(
        expr=sum(model.used[k] for k in model.K),
        sense=pyo.minimize,
    )

    # APPSI may raise RuntimeError when it cannot load a feasible solution.
    # Objective retrieval alone determines success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_frames))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
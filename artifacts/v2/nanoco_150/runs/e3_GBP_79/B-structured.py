# IR: {"sets":{"I":[0,1,2,3],"S":[0,1,2,3],"P":"{(i,j): i,j in I, i<j}","D":["left","right","below","above"]},"params":{"W":"params['sheet_width']","H":"params['sheet_length']","w":"params['billboard_widths'], length 4","h":"params['billboard_heights'], length 4"},"variables":{"used[s]":"binary","assigned[i,s]":"binary","x[i]":"continuous, 0<=x[i]<=W","y[i]":"continuous, 0<=y[i]<=H","sep[i,j,d]":"binary"},"constraints":["For each i: sum_s assigned[i,s]=1.","For each i,s: assigned[i,s]<=used[s].","For each i: x[i]+w[i]<=W and y[i]+h[i]<=H.","For each (i,j),s: sum_d sep[i,j,d]>=assigned[i,s]+assigned[j,s]-1.","For each (i,j): x[i]+w[i]<=x[j]+W*(1-sep[i,j,left]).","For each (i,j): x[j]+w[j]<=x[i]+W*(1-sep[i,j,right]).","For each (i,j): y[i]+h[i]<=y[j]+H*(1-sep[i,j,below]).","For each (i,j): y[j]+h[j]<=y[i]+H*(1-sep[i,j,above]).","For s=0,1,2: used[s]>=used[s+1]."],"objective":"minimize sum_s used[s]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sheet_width = float(params["sheet_width"])
    sheet_length = float(params["sheet_length"])
    widths = tuple(float(value) for value in params["billboard_widths"])
    heights = tuple(float(value) for value in params["billboard_heights"])

    if len(widths) != 4 or len(heights) != 4:
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 3)
    model.S = pyo.RangeSet(0, 3)
    model.P = pyo.Set(
        dimen=2,
        initialize=[
            (first, second)
            for first in range(4)
            for second in range(first + 1, 4)
        ],
    )
    model.D = pyo.Set(
        initialize=["left", "right", "below", "above"],
        ordered=True,
    )

    model.W = pyo.Param(initialize=sheet_width)
    model.H = pyo.Param(initialize=sheet_length)
    model.w = pyo.Param(
        model.I, initialize={idx: widths[idx] for idx in range(4)}
    )
    model.h = pyo.Param(
        model.I, initialize={idx: heights[idx] for idx in range(4)}
    )

    model.used = pyo.Var(model.S, domain=pyo.Binary)
    model.assigned = pyo.Var(model.I, model.S, domain=pyo.Binary)
    model.x = pyo.Var(
        model.I, domain=pyo.NonNegativeReals, bounds=(0, sheet_width)
    )
    model.y = pyo.Var(
        model.I, domain=pyo.NonNegativeReals, bounds=(0, sheet_length)
    )
    model.sep = pyo.Var(model.P, model.D, domain=pyo.Binary)

    model.assign_once = pyo.Constraint(
        model.I,
        rule=lambda mdl, idx: pyo.quicksum(
            mdl.assigned[idx, sheet] for sheet in mdl.S
        ) == 1,
    )

    model.link_sheet_usage = pyo.Constraint(
        model.I,
        model.S,
        rule=lambda mdl, idx, sheet: (
            mdl.assigned[idx, sheet] <= mdl.used[sheet]
        ),
    )

    model.width_containment = pyo.Constraint(
        model.I,
        rule=lambda mdl, idx: mdl.x[idx] + mdl.w[idx] <= mdl.W,
    )
    model.height_containment = pyo.Constraint(
        model.I,
        rule=lambda mdl, idx: mdl.y[idx] + mdl.h[idx] <= mdl.H,
    )

    # Coordinates are local to each billboard's assigned sheet.
    # A separation direction is required only for pairs sharing a sheet.
    model.require_separation = pyo.Constraint(
        model.P,
        model.S,
        rule=lambda mdl, first, second, sheet: (
            pyo.quicksum(
                mdl.sep[first, second, direction] for direction in mdl.D
            )
            >= mdl.assigned[first, sheet] + mdl.assigned[second, sheet] - 1
        ),
    )

    # Containment makes W and H valid big-M constants.
    model.left_separation = pyo.Constraint(
        model.P,
        rule=lambda mdl, first, second: (
            mdl.x[first] + mdl.w[first]
            <= mdl.x[second] + mdl.W * (1 - mdl.sep[first, second, "left"])
        ),
    )
    model.right_separation = pyo.Constraint(
        model.P,
        rule=lambda mdl, first, second: (
            mdl.x[second] + mdl.w[second]
            <= mdl.x[first] + mdl.W * (1 - mdl.sep[first, second, "right"])
        ),
    )
    model.below_separation = pyo.Constraint(
        model.P,
        rule=lambda mdl, first, second: (
            mdl.y[first] + mdl.h[first]
            <= mdl.y[second] + mdl.H * (1 - mdl.sep[first, second, "below"])
        ),
    )
    model.above_separation = pyo.Constraint(
        model.P,
        rule=lambda mdl, first, second: (
            mdl.y[second] + mdl.h[second]
            <= mdl.y[first] + mdl.H * (1 - mdl.sep[first, second, "above"])
        ),
    )

    model.sheet_order = pyo.Constraint(
        range(3),
        rule=lambda mdl, sheet: mdl.used[sheet] >= mdl.used[sheet + 1],
    )

    model.total_sheets = pyo.Objective(
        expr=pyo.quicksum(model.used[sheet] for sheet in model.S),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_sheets))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
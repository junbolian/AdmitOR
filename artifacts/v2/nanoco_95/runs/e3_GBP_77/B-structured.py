# IR: {
#   "sets": {"I": [1,2,3,4], "S": [1,2,3,4], "P": "all (i,j) in I with i<j", "D": ["left","right","below","above"]},
#   "params": {"W": "params['sheet_width']", "H": "params['sheet_height']", "w[i]": "params['part_widths'][i-1]", "h[i]": "params['part_heights'][i-1]"},
#   "variables": {"assigned[i,s]": "binary", "used[s]": "binary", "x[i]": "nonnegative real", "y[i]": "nonnegative real", "separated[i,j,d]": "binary"},
#   "constraints": [
#     "sum_s assigned[i,s] = 1 for each i",
#     "assigned[i,s] <= used[s] for each i,s",
#     "used[s] <= sum_i assigned[i,s] for each s",
#     "x[i] + w[i] <= W for each i",
#     "y[i] + h[i] <= H for each i",
#     "sum_d separated[i,j,d] <= 1 for each (i,j)",
#     "sum_d separated[i,j,d] >= assigned[i,s] + assigned[j,s] - 1 for each (i,j),s",
#     "x[i] + w[i] <= x[j] + W*(1-separated[i,j,'left']) for each (i,j)",
#     "x[j] + w[j] <= x[i] + W*(1-separated[i,j,'right']) for each (i,j)",
#     "y[i] + h[i] <= y[j] + H*(1-separated[i,j,'below']) for each (i,j)",
#     "y[j] + h[j] <= y[i] + H*(1-separated[i,j,'above']) for each (i,j)"
#   ],
#   "objective": "minimize sum_s used[s]"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sheet_width = params["sheet_width"]
    sheet_height = params["sheet_height"]
    part_widths = list(params["part_widths"])
    part_heights = list(params["part_heights"])

    if len(part_widths) != 4 or len(part_heights) != 4:
        return {"objective": None, "status": "invalid_part_count"}

    model = pyo.ConcreteModel()

    # Four candidate sheets suffice: each of the four parts can use its own.
    model.parts = pyo.RangeSet(1, 4)
    model.sheets = pyo.RangeSet(1, 4)
    model.pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 5)
            for j in range(i + 1, 5)
        ],
    )
    model.directions = pyo.Set(
        initialize=["left", "right", "below", "above"]
    )

    model.sheet_width = pyo.Param(
        initialize=sheet_width, within=pyo.PositiveReals
    )
    model.sheet_height = pyo.Param(
        initialize=sheet_height, within=pyo.PositiveReals
    )
    model.part_width = pyo.Param(
        model.parts,
        initialize={i: part_widths[i - 1] for i in range(1, 5)},
        within=pyo.PositiveReals,
    )
    model.part_height = pyo.Param(
        model.parts,
        initialize={i: part_heights[i - 1] for i in range(1, 5)},
        within=pyo.PositiveReals,
    )

    model.assigned = pyo.Var(
        model.parts, model.sheets, domain=pyo.Binary
    )
    model.used = pyo.Var(model.sheets, domain=pyo.Binary)
    model.x = pyo.Var(model.parts, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.parts, domain=pyo.NonNegativeReals)
    model.separated = pyo.Var(
        model.pairs, model.directions, domain=pyo.Binary
    )

    model.assignment_once = pyo.Constraint(
        model.parts,
        rule=lambda mdl, i: sum(
            mdl.assigned[i, s] for s in mdl.sheets
        ) == 1,
    )
    model.assignment_requires_sheet = pyo.Constraint(
        model.parts,
        model.sheets,
        rule=lambda mdl, i, s: mdl.assigned[i, s] <= mdl.used[s],
    )
    model.used_sheet_has_part = pyo.Constraint(
        model.sheets,
        rule=lambda mdl, s: mdl.used[s] <= sum(
            mdl.assigned[i, s] for i in mdl.parts
        ),
    )

    # Coordinates are local to the sheet assigned to each part.
    # Fixed dimensions enforce the required orientation.
    model.width_containment = pyo.Constraint(
        model.parts,
        rule=lambda mdl, i: (
            mdl.x[i] + mdl.part_width[i] <= mdl.sheet_width
        ),
    )
    model.height_containment = pyo.Constraint(
        model.parts,
        rule=lambda mdl, i: (
            mdl.y[i] + mdl.part_height[i] <= mdl.sheet_height
        ),
    )

    model.at_most_one_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: sum(
            mdl.separated[i, j, d] for d in mdl.directions
        ) <= 1,
    )
    model.same_sheet_requires_separation = pyo.Constraint(
        model.pairs,
        model.sheets,
        rule=lambda mdl, i, j, s: sum(
            mdl.separated[i, j, d] for d in mdl.directions
        ) >= mdl.assigned[i, s] + mdl.assigned[j, s] - 1,
    )

    # Containment makes sheet width and height valid big-M values.
    model.left_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: (
            mdl.x[i] + mdl.part_width[i]
            <= mdl.x[j]
            + mdl.sheet_width * (1 - mdl.separated[i, j, "left"])
        ),
    )
    model.right_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: (
            mdl.x[j] + mdl.part_width[j]
            <= mdl.x[i]
            + mdl.sheet_width * (1 - mdl.separated[i, j, "right"])
        ),
    )
    model.below_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: (
            mdl.y[i] + mdl.part_height[i]
            <= mdl.y[j]
            + mdl.sheet_height * (1 - mdl.separated[i, j, "below"])
        ),
    )
    model.above_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, i, j: (
            mdl.y[j] + mdl.part_height[j]
            <= mdl.y[i]
            + mdl.sheet_height * (1 - mdl.separated[i, j, "above"])
        ),
    )

    model.total_sheets = pyo.Objective(
        expr=sum(model.used[s] for s in model.sheets),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_sheets))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
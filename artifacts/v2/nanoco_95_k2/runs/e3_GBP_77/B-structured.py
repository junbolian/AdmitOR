# IR: {"sets":{"parts":[0,1,2,3],"sheets":[0,1,2,3],"pairs":"(i,j) with i<j","directions":["left","right","below","above"]},"params":{"sheet_width":"params['sheet_width']","sheet_height":"params['sheet_height']","part_widths":"params['part_widths'], indexed by parts","part_heights":"params['part_heights'], indexed by parts"},"variables":{"used[s]":"binary","assigned[i,s]":"binary","x[i]":"nonnegative real","y[i]":"nonnegative real","separated[i,j,d]":"binary"},"constraints":["sum_s assigned[i,s] = 1 for each part i","assigned[i,s] <= used[s] for each i,s","x[i] + part_widths[i] <= sheet_width for each i","y[i] + part_heights[i] <= sheet_height for each i","sum_d separated[i,j,d] >= assigned[i,s] + assigned[j,s] - 1 for each pair i,j and sheet s","x[i] + part_widths[i] <= x[j] + sheet_width*(1-separated[i,j,left]) for each pair i,j","x[j] + part_widths[j] <= x[i] + sheet_width*(1-separated[i,j,right]) for each pair i,j","y[i] + part_heights[i] <= y[j] + sheet_height*(1-separated[i,j,below]) for each pair i,j","y[j] + part_heights[j] <= y[i] + sheet_height*(1-separated[i,j,above]) for each pair i,j"],"objective":"minimize sum_s used[s]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Four sheets suffice whenever every individual part fits a sheet.
    model = pyo.ConcreteModel()

    model.parts = pyo.Set(initialize=range(4), ordered=True)
    model.sheets = pyo.Set(initialize=range(4), ordered=True)
    model.pairs = pyo.Set(
        dimen=2,
        initialize=[
            (first, second)
            for first in range(4)
            for second in range(first + 1, 4)
        ],
    )
    model.directions = pyo.Set(
        initialize=["left", "right", "below", "above"],
        ordered=True,
    )

    model.sheet_width = pyo.Param(
        initialize=params["sheet_width"],
        within=pyo.PositiveReals,
    )
    model.sheet_height = pyo.Param(
        initialize=params["sheet_height"],
        within=pyo.PositiveReals,
    )
    model.part_widths = pyo.Param(
        model.parts,
        initialize={
            part: params["part_widths"][part]
            for part in range(4)
        },
        within=pyo.PositiveReals,
    )
    model.part_heights = pyo.Param(
        model.parts,
        initialize={
            part: params["part_heights"][part]
            for part in range(4)
        },
        within=pyo.PositiveReals,
    )

    model.used = pyo.Var(model.sheets, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.parts, model.sheets, domain=pyo.Binary
    )
    model.x = pyo.Var(model.parts, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.parts, domain=pyo.NonNegativeReals)
    model.separated = pyo.Var(
        model.pairs, model.directions, domain=pyo.Binary
    )

    model.assign_once = pyo.Constraint(
        model.parts,
        rule=lambda mdl, part: sum(
            mdl.assigned[part, sheet] for sheet in mdl.sheets
        ) == 1,
    )
    model.require_used_sheet = pyo.Constraint(
        model.parts,
        model.sheets,
        rule=lambda mdl, part, sheet:
            mdl.assigned[part, sheet] <= mdl.used[sheet],
    )
    model.horizontal_boundary = pyo.Constraint(
        model.parts,
        rule=lambda mdl, part:
            mdl.x[part] + mdl.part_widths[part] <= mdl.sheet_width,
    )
    model.vertical_boundary = pyo.Constraint(
        model.parts,
        rule=lambda mdl, part:
            mdl.y[part] + mdl.part_heights[part] <= mdl.sheet_height,
    )

    # Coordinates are local to the sheet assigned to each part.
    # A pair sharing a sheet must satisfy at least one separation.
    model.require_separation = pyo.Constraint(
        model.pairs,
        model.sheets,
        rule=lambda mdl, first, second, sheet: sum(
            mdl.separated[first, second, direction]
            for direction in mdl.directions
        ) >= (
            mdl.assigned[first, sheet]
            + mdl.assigned[second, sheet]
            - 1
        ),
    )

    # Sheet dimensions are valid big-M values because all parts
    # must satisfy the sheet boundary constraints.
    model.left_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, first, second:
            mdl.x[first] + mdl.part_widths[first]
            <= mdl.x[second] + mdl.sheet_width * (
                1 - mdl.separated[first, second, "left"]
            ),
    )
    model.right_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, first, second:
            mdl.x[second] + mdl.part_widths[second]
            <= mdl.x[first] + mdl.sheet_width * (
                1 - mdl.separated[first, second, "right"]
            ),
    )
    model.below_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, first, second:
            mdl.y[first] + mdl.part_heights[first]
            <= mdl.y[second] + mdl.sheet_height * (
                1 - mdl.separated[first, second, "below"]
            ),
    )
    model.above_separation = pyo.Constraint(
        model.pairs,
        rule=lambda mdl, first, second:
            mdl.y[second] + mdl.part_heights[second]
            <= mdl.y[first] + mdl.sheet_height * (
                1 - mdl.separated[first, second, "above"]
            ),
    )

    model.total_sheets = pyo.Objective(
        expr=sum(model.used[sheet] for sheet in model.sheets),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Preserve unexpected solver or programming exceptions.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_sheets))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
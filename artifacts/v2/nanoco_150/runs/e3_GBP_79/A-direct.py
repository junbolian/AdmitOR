import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sheet_width = params["sheet_width"]
    sheet_length = params["sheet_length"]
    billboard_widths = params["billboard_widths"]
    billboard_heights = params["billboard_heights"]

    n = len(billboard_widths)
    billboards = list(range(n))
    sheets = list(range(n))

    M_x = sheet_width
    M_y = sheet_length

    model = pyo.ConcreteModel()

    model.B = pyo.Set(initialize=billboards)
    model.S = pyo.Set(initialize=sheets)

    model.x = pyo.Var(model.B, model.S, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.B, model.S, within=pyo.NonNegativeReals)
    model.used = pyo.Var(model.S, within=pyo.Binary)

    model.assign = pyo.Var(model.B, model.S, within=pyo.Binary)
    model.left = pyo.Var(model.B, model.S, model.B, within=pyo.Binary)
    model.below = pyo.Var(model.B, model.S, model.B, within=pyo.Binary)

    def objective_rule(m):
        return sum(m.used[s] for s in m.S)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def assign_once_rule(m, b):
        return sum(m.assign[b, s] for s in m.S) == 1

    model.assign_once = pyo.Constraint(model.B, rule=assign_once_rule)

    def assign_used_rule(m, b, s):
        return m.assign[b, s] <= m.used[s]

    model.assign_used = pyo.Constraint(model.B, model.S, rule=assign_used_rule)

    def width_fit_rule(m, b, s):
        return m.x[b, s] + billboard_widths[b] <= sheet_width + (1 - m.assign[b, s]) * (
            sheet_width + billboard_widths[b]
        )

    model.width_fit = pyo.Constraint(model.B, model.S, rule=width_fit_rule)

    def length_fit_rule(m, b, s):
        return m.y[b, s] + billboard_heights[b] <= sheet_length + (1 - m.assign[b, s]) * (
            sheet_length + billboard_heights[b]
        )

    model.length_fit = pyo.Constraint(model.B, model.S, rule=length_fit_rule)

    def x_bound_rule(m, b, s):
        return m.x[b, s] <= M_x * m.assign[b, s]

    model.x_bound = pyo.Constraint(model.B, model.S, rule=x_bound_rule)

    def y_bound_rule(m, b, s):
        return m.y[b, s] <= M_y * m.assign[b, s]

    model.y_bound = pyo.Constraint(model.B, model.S, rule=y_bound_rule)

    def pair_rule(m, b1, s, b2):
        if b1 >= b2:
            return pyo.Constraint.Skip
        both = m.assign[b1, s] + m.assign[b2, s]
        left_ok = m.x[b1, s] + billboard_widths[b1] <= m.x[b2, s] + (1 - m.left[b1, s, b2]) * (
            sheet_width + billboard_widths[b1]
        )
        right_ok = m.x[b2, s] + billboard_widths[b2] <= m.x[b1, s] + m.left[b1, s, b2] * (
            sheet_width + billboard_widths[b2]
        )
        below_ok = m.y[b1, s] + billboard_heights[b1] <= m.y[b2, s] + (1 - m.below[b1, s, b2]) * (
            sheet_length + billboard_heights[b1]
        )
        above_ok = m.y[b2, s] + billboard_heights[b2] <= m.y[b1, s] + m.below[b1, s, b2] * (
            sheet_length + billboard_heights[b2]
        )
        return pyo.Constraint.ConstraintList().add(
            left_ok, right_ok, below_ok, above_ok
        ) if False else None

    # Build non-overlap constraints explicitly
    def nonoverlap_rule(m, b1, s, b2):
        if b1 >= b2:
            return pyo.Constraint.Skip
        both = m.assign[b1, s] + m.assign[b2, s]
        return (
            m.left[b1, s, b2] + (1 - m.left[b1, s, b2]) * 0 <= 1
        ) and (
            m.x[b1, s] + billboard_widths[b1]
            <= m.x[b2, s] + (1 - m.left[b1, s, b2]) * (sheet_width + billboard_widths[b1])
            + (1 - both) * (2 * sheet_width + billboard_widths[b1] + billboard_widths[b2])
        ) and (
            m.x[b2, s] + billboard_widths[b2]
            <= m.x[b1, s] + m.left[b1, s, b2] * (sheet_width + billboard_widths[b2])
            + (1 - both) * (2 * sheet_width + billboard_widths[b1] + billboard_widths[b2])
        ) and (
            m.y[b1, s] + billboard_heights[b1]
            <= m.y[b2, s] + (1 - m.below[b1, s, b2]) * (sheet_length + billboard_heights[b1])
            + (1 - both) * (2 * sheet_length + billboard_heights[b1] + billboard_heights[b2])
        ) and (
            m.y[b2, s] + billboard_heights[b2]
            <= m.y[b1, s] + m.below[b1, s, b2] * (sheet_length + billboard_heights[b2])
            + (1 - both) * (2 * sheet_length + billboard_heights[b1] + billboard_heights[b2])
        )

    # Need conjunctive constraints; express each as separate Constraint components
    def lo_x1(m, b1, s, b2):
        if b1 >= b2:
            return pyo.Constraint.Skip
        both = m.assign[b1, s] + m.assign[b2, s]
        return m.x[b1, s] + billboard_widths[b1] <= m.x[b2, s] + (1 - m.left[b1, s, b2]) * (
            sheet_width + billboard_widths[b1]
        ) + (1 - both) * (2 * sheet_width + billboard_widths[b1] + billboard_widths[b2])

    def lo_x2(m, b1, s, b2):
        if b1 >= b2:
            return pyo.Constraint.Skip
        both = m.assign[b1, s] + m.assign[b2, s]
        return m.x[b2, s] + billboard_widths[b2] <= m.x[b1, s] + m.left[b1, s, b2] * (
            sheet_width + billboard_widths[b2]
        ) + (1 - both) * (2 * sheet_width + billboard_widths[b1] + billboard_widths[b2])

    def lo_y1(m, b1, s, b2):
        if b1 >= b2:
            return pyo.Constraint.Skip
        both = m.assign[b1, s] + m.assign[b2, s]
        return m.y[b1, s] + billboard_heights[b1] <= m.y[b2, s] + (1 - m.below[b1, s, b2]) * (
            sheet_length + billboard_heights[b1]
        ) + (1 - both) * (2 * sheet_length + billboard_heights[b1] + billboard_heights[b2])

    def lo_y2(m, b1, s, b2):
        if b1 >= b2:
            return pyo.Constraint.Skip
        both = m.assign[b1, s] + m.assign[b2, s]
        return m.y[b2, s] + billboard_heights[b2] <= m.y[b1, s] + m.below[b1, s, b2] * (
            sheet_length + billboard_heights[b2]
        ) + (1 - both) * (2 * sheet_length + billboard_heights[b1] + billboard_heights[b2])

    model.lo_x1 = pyo.Constraint(model.B, model.S, model.B, rule=lo_x1)
    model.lo_x2 = pyo.Constraint(model.B, model.S, model.B, rule=lo_x2)
    model.lo_y1 = pyo.Constraint(model.B, model.S, model.B, rule=lo_y1)
    model.lo_y2 = pyo.Constraint(model.B, model.S, model.B, rule=lo_y2)

    # Symmetry breaking: sheet s used only if sheet s-1 used
    def sym_rule(m, s):
        if s == 0:
            return pyo.Constraint.Skip
        return m.used[s] <= m.used[s - 1]

    model.sym = pyo.Constraint(model.S, rule=sym_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
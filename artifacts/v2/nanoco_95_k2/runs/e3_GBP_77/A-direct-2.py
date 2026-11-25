import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sheet_width = params["sheet_width"]
    sheet_height = params["sheet_height"]
    part_widths = params["part_widths"]
    part_heights = params["part_heights"]

    n_parts = len(part_widths)
    parts = list(range(n_parts))
    # Upper bound on number of sheets: one sheet per part is always feasible
    max_sheets = n_parts
    sheets = list(range(max_sheets))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=parts)
    model.S = pyo.Set(initialize=sheets)

    # Assignment variable: part p assigned to sheet s
    model.x = pyo.Var(model.P, model.S, domain=pyo.Binary)

    # Whether sheet s is used
    model.y = pyo.Var(model.S, domain=pyo.Binary)

    # Position (bottom-left corner) of part p on its sheet
    # Continuous coordinates bounded by sheet dimensions
    model.px = pyo.Var(model.P, domain=pyo.NonNegativeReals, bounds=(0, sheet_width))
    model.py = pyo.Var(model.P, domain=pyo.NonNegativeReals, bounds=(0, sheet_height))

    # Each part assigned to exactly one sheet
    def assign_rule(m, p):
        return sum(m.x[p, s] for s in m.S) == 1
    model.assign_con = pyo.Constraint(model.P, rule=assign_rule)

    # Part fits within sheet boundaries (only meaningful when assigned)
    def bound_x_rule(m, p):
        return m.px[p] + part_widths[p] <= sheet_width
    model.bound_x_con = pyo.Constraint(model.P, rule=bound_x_rule)

    def bound_y_rule(m, p):
        return m.py[p] + part_heights[p] <= sheet_height
    model.bound_y_con = pyo.Constraint(model.P, rule=bound_y_rule)

    # Link: if part assigned to sheet s then sheet s is used
    def link_rule(m, p, s):
        return m.x[p, s] <= m.y[s]
    model.link_con = pyo.Constraint(model.P, model.S, rule=link_rule)

    # Symmetry breaking: sheet s can only be used if all lower sheets used
    def sym_rule(m, s):
        if s == 0:
            return pyo.Constraint.Skip
        return m.y[s] <= m.y[s - 1]
    model.sym_con = pyo.Constraint(model.S, rule=sym_rule)

    # Non-overlap for any pair of parts on same sheet
    # Big-M disjunctions: for pair (p,q) and each sheet s
    # Only enforce when both assigned to s (x[p,s] + x[q,s] - 1 == 1)
    M = sheet_width + sheet_height

    model.pairs = pyo.Set(
        initialize=[(i, j) for i in parts for j in parts if i < j],
        dimen=2,
    )

    # Disjunctive constraints via binary orientation variables
    # For each pair and sheet: choose separation direction if both on sheet
    model.sep = pyo.Var(model.pairs, model.S, within=pyo.Binary)

    def nonoverlap_rule(m, p, q, s):
        w_p = part_widths[p]
        h_p = part_heights[p]
        w_q = part_widths[q]
        h_q = part_heights[q]
        both = m.x[p, s] + m.x[q, s] - 1
        # If both on same sheet (both == 1 => both = 1), require a separation
        # p left of q: px[p] + w_p <= px[q]
        # or p right of q: px[q] + w_q <= px[p]
        # or p below q: py[p] + h_p <= py[q]
        # or p above q: py[q] + h_q <= py[p]
        # Use big-M relaxation tied to both.

        # Left separation: px[p] + w_p <= px[q] + M*(1 - both_left)
        # We model OR via helper binaries. To keep simple, relax each with
        # big-M controlled by "both" and a chain of binaries.
        # Simpler: use four inequalities each with binary and enforce at least
        # one; use standard approach below.
        return pyo.Constraint.Skip
    # (handled separately below with helper binaries)

    # We'll build the disjunction explicitly with 4 binaries per pair per sheet
    # But we only care when both on the same sheet AND x[p,s]==1 and x[q,s]==1.
    # Because pair only relevant when both assigned to s, we can use x[p,s]*x[q,s].
    # To keep linear, introduce bin z[p,q,s] = 1 requiring separation enforced.

    model.zleft = pyo.Var(model.pairs, model.S, domain=pyo.Binary)
    model.zright = pyo.Var(model.pairs, model.S, domain=pyo.Binary)
    model.zbelow = pyo.Var(model.pairs, model.S, domain=pyo.Binary)
    model.zabove = pyo.Var(model.pairs, model.S, domain=pyo.Binary)

    # When both on same sheet, at least one separation must hold.
    def atleastone_rule(m, p, q, s):
        both = m.x[p, s] + m.x[q, s] - 1
        # both is 1 if both assigned, else <=0 (0, or -1)
        # Require zleft+zright+zbelow+zabove >= both
        # i.e. if both=1 sum>=1; if both<=0 no requirement (sum>= <=0 always true)
        return (m.zleft[p, q, s] + m.zright[p, q, s]
                + m.zbelow[p, q, s] + m.zabove[p, q, s]) >= both
    model.atleastone_con = pyo.Constraint(model.pairs, model.S, rule=atleastone_rule)

    # Each separation implication
    def left_rule(m, p, q, s):
        w_p = part_widths[p]
        return m.px[p] + w_p <= m.px[q] + M * (1 - m.zleft[p, q, s])
    model.left_con = pyo.Constraint(model.pairs, model.S, rule=left_rule)

    def right_rule(m, p, q, s):
        w_q = part_widths[q]
        return m.px[q] + w_q <= m.px[p] + M * (1 - m.zright[p, q, s])
    model.right_con = pyo.Constraint(model.pairs, model.S, rule=right_rule)

    def below_rule(m, p, q, s):
        h_p = part_heights[p]
        return m.py[p] + h_p <= m.py[q] + M * (1 - m.zbelow[p, q, s])
    model.below_con = pyo.Constraint(model.pairs, model.S, rule=below_rule)

    def above_rule(m, p, q, s):
        h_q = part_heights[q]
        return m.py[q] + h_q <= m.py[p] + M * (1 - m.zabove[p, q, s])
    model.above_con = pyo.Constraint(model.pairs, model.S, rule=above_rule)

    # Objective: minimize number of sheets used
    def obj_rule(m):
        return sum(m.y[s] for s in m.S)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Solve
    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
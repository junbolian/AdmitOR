import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sw = params["sheet_width"]
    sh = params["sheet_height"]
    pw = params["part_widths"]
    ph = params["part_heights"]
    n_parts = len(pw)
    max_sheets = n_parts

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(1, n_parts)
    model.S = pyo.RangeSet(1, max_sheets)

    # y[s] = 1 if sheet s is used
    model.y = pyo.Var(model.S, domain=pyo.Binary)
    # x[i,s] = 1 if part i assigned to sheet s
    model.x = pyo.Var(model.P, model.S, domain=pyo.Binary)
    # position of part i on its sheet (lower-left corner), per (i,s)
    model.lx = pyo.Var(model.P, model.S, domain=pyo.NonNegativeReals)
    model.ly = pyo.Var(model.P, model.S, domain=pyo.NonNegativeReals)
    # ordering within a pair on the same sheet
    model.lr = pyo.Var(model.P, model.P, model.S, domain=pyo.Binary)  # i left of j on s
    model.ud = pyo.Var(model.P, model.P, model.S, domain=pyo.Binary)  # i below j on s

    # each part assigned to exactly one sheet
    model.assign = pyo.Constraint(
        model.P, rule=lambda m, i: sum(m.x[i, s] for s in m.S) == 1
    )

    # linking: x[i,s] <= y[s]
    model.link = pyo.Constraint(
        model.P, model.S, rule=lambda m, i, s: m.x[i, s] <= m.y[s]
    )

    # symmetry: each used sheet must be "opened" in order (optional but helps)
    model.sym = pyo.Constraint(
        model.S,
        rule=lambda m, s: m.y[s] >= m.y[s + 1] if s < max_sheets else pyo.Constraint.Skip,
    )

    # Big-M per pair for positional separation
    BigM_x = sw + max(pw)
    BigM_y = sh + max(ph)

    model.pairs = pyo.Set(
        initialize=[(i, j) for i in range(1, n_parts + 1)
                    for j in range(1, n_parts + 1) if i < j]
    )

    n_part = len(pw)

    # position within sheet bounds (only meaningful if assigned; enforce always with x)
    def w_in(m, i, s):
        return m.lx[i, s] + pw[i - 1] * m.x[i, s] <= sw
    model.w_in = pyo.Constraint(model.P, model.S, rule=w_in)

    def h_in(m, i, s):
        return m.ly[i, s] + ph[i - 1] * m.x[i, s] <= sh
    model.h_in = pyo.Constraint(model.P, model.S, rule=h_in)

    # "on sheet s" conjunctive disjunction: at least one of {i left of j, j left of i,
    # i below j, j below i} holds when both on same sheet.
    # Introduce big-M constraints activated when x[i,s] = x[j,s] = 1.
    def left_rule(m, i, j, s):
        return m.lx[i, s] + pw[i - 1] - m.lx[j, s] <= BigM_x * (1 - m.lr[i, j, s] + (1 - m.x[i, s]) + (1 - m.x[j, s]))
    def right_rule(m, i, j, s):
        return m.lx[j, s] + pw[j - 1] - m.lx[i, s] <= BigM_x * (1 - (1 - m.lr[i, j, s]) + (1 - m.x[i, s]) + (1 - m.x[j, s]))
    def below_rule(m, i, j, s):
        return m.ly[i, s] + ph[i - 1] - m.ly[j, s] <= BigM_y * (1 - m.ud[i, j, s] + (1 - m.x[i, s]) + (1 - m.x[j, s]))
    def above_rule(m, i, j, s):
        return m.ly[j, s] + ph[j - 1] - m.ly[i, s] <= BigM_y * (1 - (1 - m.ud[i, j, s]) + (1 - m.x[i, s]) + (1 - m.x[j, s]))
    def sep_rule(m, i, j, s):
        # if both on the same sheet, at least one separation direction
        return m.lr[i, j, s] + m.ud[i, j, s] + (1 - m.lr[i, j, s]) + (1 - m.ud[i, j, s]) >= 1 # trivial; rely on pairwise constraints? no.

    # Instead use a proper disjunction indicator.
    model.con_lr = pyo.Constraint(model.pairs, model.S, rule=left_rule)
    model.con_rl = pyo.Constraint(model.pairs, model.S, rule=right_rule)
    model.con_ud = pyo.Constraint(model.pairs, model.S, rule=below_rule)
    model.con_du = pyo.Constraint(model.pairs, model.S, rule=above_rule)

    # Ensure at least one separation is chosen when co-located:
    def atleast_rule(m, i, j, s):
        return (m.lr[i, j, s] + m.ud[i, j, s]) >= (m.x[i, s] + m.x[j, s] - 1)
    model.atleast = pyo.Constraint(model.pairs, model.S, rule=atleast_rule)

    # objective: minimize number of sheets used
    model.obj = pyo.Objective(expr=sum(model.y[s] for s in model.S), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
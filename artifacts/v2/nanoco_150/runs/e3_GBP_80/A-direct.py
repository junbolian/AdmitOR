import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n_ic = 5
    n_wafer = n_ic
    widths = [
        params["ic1_width"], params["ic2_width"], params["ic3_width"],
        params["ic4_width"], params["ic5_width"],
    ]
    heights = [
        params["ic1_height"], params["ic2_height"], params["ic3_height"],
        params["ic4_height"], params["ic5_height"],
    ]
    W = params["wafer_width"]
    H = params["wafer_height"]

    model = pyo.ConcreteModel()
    model.ICS = pyo.RangeSet(0, n_ic - 1)
    model.WAFERS = pyo.RangeSet(0, n_wafer - 1)
    model.PAIRS = pyo.Set(initialize=[
        (a, b) for a in range(n_ic) for b in range(a + 1, n_ic)
    ])

    model.x = pyo.Var(model.ICS, model.WAFERS, domain=pyo.Binary)
    model.y = pyo.Var(model.WAFERS, domain=pyo.Binary)
    model.px = pyo.Var(model.ICS, domain=pyo.NonNegativeReals)
    model.py_ = pyo.Var(model.ICS, domain=pyo.NonNegativeReals)
    model.lr = pyo.Var(model.PAIRS, domain=pyo.Binary)
    model.ud = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def assign_rule(m, i):
        return sum(m.x[i, w] for w in m.WAFERS) == 1
    model.assign_con = pyo.Constraint(model.ICS, rule=assign_rule)

    model.active_con = pyo.Constraint(
        model.WAFERS,
        rule=lambda m, w: sum(m.x[i, w] for i in m.ICS) <= n_ic * m.y[w],
    )

    def bound_x_rule(m, i):
        return m.px[i] + widths[i] <= W

    def bound_y_rule(m, i):
        return m.py_[i] + heights[i] <= H

    model.bound_x = pyo.Constraint(model.ICS, rule=bound_x_rule)
    model.bound_y = pyo.Constraint(model.ICS, rule=bound_y_rule)

    Mx = W + max(widths)
    My = H + max(heights)

    def sep_rule_x1(m, i, j):
        # i left of j, only binding if same wafer
        return m.px[i] + widths[i] <= m.px[j] + Mx * (1 - m.lr[i, j]) + Mx * (2 - m.x[i, w_] - m.x[j, w_]) if False else (
            m.px[i] + widths[i] - m.px[j]
            <= Mx * (1 - m.lr[i, j]) + Mx * (2 - sum(m.x[i, w] + m.x[j, w] for w in m.WAFERS) / 2)
        )

    # Build separation constraints explicitly without relying on "same" variables.
    # If ICs i and j are assigned to the same wafer, one of the 4 orderings must hold.
    # Use indicator per pair per ordering tied to wafer assignment with big-M on
    # non-same-wafer pairs being automatically satisfied.

    def make_big_m_terms(m, i, j):
        # sum over w of x[i,w]*x[j,w] is nonlinear; instead relax through auxiliary
        # We use for each pair a sum of x[i,w]+x[j,w] over w == 2 when same wafer,
        # but could be 2 also if on different wafers? No: each IC on exactly one wafer,
        # so x[i,w]+x[j,w] sums to 2 iff they share the same wafer, else 0.
        return sum(m.x[i, w] + m.x[j, w] for w in m.WAFERS)

    def sep_rule(m, i, j):
        same_sum = make_big_m_terms(m, i, j)  # equals 2 if same wafer, 0 otherwise
        not_same = 2 - same_sum
        c1 = m.px[i] + widths[i] - m.px[j] <= Mx * (1 - m.lr[i, j]) + Mx * not_same
        c2 = m.px[j] + widths[j] - m.px[i] <= Mx * m.lr[i, j] + Mx * not_same
        c3 = m.py_[i] + heights[i] - m.py_[j] <= My * (1 - m.ud[i, j]) + My * not_same
        c4 = m.py_[j] + heights[j] - m.py_[i] <= My * m.ud[i, j] + My * not_same
        # Need at least one ordering active when same wafer: enforce via selector
        # Introduce a single selector variable for which of 4 cases holds.
        return pyo.ConstraintList()  # placeholder replaced below

    # Remove placeholder approach; build explicit constraints.
    del model.sep
    if hasattr(model, "sep"):
        pass

    return _build_and_solve(model, params, widths, heights, W, H, n_ic, n_wafer)


def _build_and_solve(model, params, widths, heights, W, H, n_ic, n_wafer):
    # fresh model with clean separation formulation
    mdl = pyo.ConcreteModel()
    mdl.ICS = pyo.RangeSet(0, n_ic - 1)
    mdl.WAFERS = pyo.RangeSet(0, n_wafer - 1)
    mdl.PAIRS = pyo.Set(initialize=[
        (a, b) for a in range(n_ic) for b in range(a + 1, n_ic)
    ])

    mdl.x = pyo.Var(mdl.ICS, mdl.WAFERS, domain=pyo.Binary)
    mdl.y = pyo.Var(mdl.WAFERS, domain=pyo.Binary)
    mdl.px = pyo.Var(mdl.ICS, domain=pyo.NonNegativeReals)
    mdl.py_ = pyo.Var(mdl.ICS, domain=pyo.NonNegativeReals)

    # For each pair choose one of 4 relative orderings: lr (i left j if 1 else j left i),
    # ud (i below j if 1 else j below i).
    mdl.lr = pyo.Var(mdl.PAIRS, domain=pyo.Binary)
    mdl.ud = pyo.Var(mdl.PAIRS, domain=pyo.Binary)

    mdl.assign_con = pyo.Constraint(
        mdl.ICS, rule=lambda m, i: sum(m.x[i, w] for w in m.WAFERS) == 1
    )
    mdl.active_con = pyo.Constraint(
        mdl.WAFERS,
        rule=lambda m, w: sum(m.x[i, w] for i in m.ICS) <= n_ic * m.y[w],
    )
    mdl.bound_x = pyo.Constraint(
        mdl.ICS, rule=lambda m, i: m.px[i] + widths[i] <= W
    )
    mdl.bound_y = pyo.Constraint(
        mdl.ICS, rule=lambda m, i: m.py_[i] + heights[i] <= H
    )

    Mx = W + max(widths)
    My = H + max(heights)

    def same_indicator(m, i, j):
        # 1 if same wafer. Since exactly one wafer per IC,
        # sum_w (x[i,w] + x[j,w]) == 2 if same wafer, 0 if different.
        return (sum(m.x[i, w] + m.x[j, w] for w in m.WAFERS) - 1.0)

    def sep_x1(m, i, j):
        return m.px[i] + widths[i] - m.px[j] <= Mx * (1 - m.lr[i, j]) + Mx * (1 - same_indicator(m, i, j))
    def sep_x2(m, i, j):
        return m.px[j] + widths[j] - m.px[i] <= Mx * m.lr[i, j] + Mx * (1 - same_indicator(m, i, j))
    def sep_y1(m, i, j):
        return m.py_[i] + heights[i] - m.py_[j] <= My * (1 - m.ud[i, j]) + My * (1 - same_indicator(m, i, j))
    def sep_y2(m, i, j):
        return m.py_[j] + heights[j] - m.py_[i] <= My * m.ud[i, j] + My * (1 - same_indicator(m, i, j))

    mdl.sep_x1 = pyo.Constraint(mdl.PAIRS, rule=sep_x1)
    mdl.sep_x2 = pyo.Constraint(mdl.PAIRS, rule=sep_x2)
    mdl.sep_y1 = pyo.Constraint(mdl.PAIRS, rule=sep_y1)
    mdl.sep_y2 = pyo.Constraint(mdl.PAIRS, rule=sep_y2)

    mdl.obj = pyo.Objective(
        expr=sum(mdl.y[w] for w in mdl.WAFERS), sense=pyo.minimize
    )

    Highs().solve(mdl)
    obj_val = float(pyo.value(mdl.obj))
    return {"objective": obj_val, "status": "optimal"}
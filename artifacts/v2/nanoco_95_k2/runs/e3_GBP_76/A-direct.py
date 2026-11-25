import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hide_width = params["hide_width"]
    hide_height = params["hide_height"]
    patch_widths = params["patch_widths"]
    patch_heights = params["patch_heights"]

    n = len(patch_widths)

    # Upper bound on hides: place each patch on its own hide
    max_hides = n

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n - 1)
    model.H = pyo.RangeSet(0, max_hides - 1)

    # Assignment of patch p to hide h
    model.assign = pyo.Var(model.P, model.H, domain=pyo.Binary)

    # Hide used indicator
    model.used = pyo.Var(model.H, domain=pyo.Binary)

    # Position of patch p (only meaningful for its assigned hide)
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    # Relative position binaries for pairs of patches
    # left[p,q] = 1 means p is to the left of q
    # below[p,q] = 1 means p is below q
    pairs = [(p, q) for p in range(n) for q in range(n) if p < q]
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.left = pyo.Var(model.pairs, domain=pyo.Binary)
    model.below = pyo.Var(model.pairs, domain=pyo.Binary)

    # Each patch assigned to exactly one hide
    def assign_rule(m, p):
        return sum(m.assign[p, h] for h in m.H) == 1
    model.assign_con = pyo.Constraint(model.P, rule=assign_rule)

    # used[h] >= assign[p,h]
    def used_rule(m, p, h):
        return m.assign[p, h] <= m.used[h]
    model.used_con = pyo.Constraint(model.P, model.H, rule=used_rule)

    # Bounds within hide
    def xbound_rule(m, p):
        return m.x[p] + patch_widths[p] <= hide_width
    model.xb_con = pyo.Constraint(model.P, rule=xbound_rule)

    def ybound_rule(m, p):
        return m.y[p] + patch_heights[p] <= hide_height
    model.yb_con = pyo.Constraint(model.P, rule=ybound_rule)

    # Non-overlap: at least one separating direction must hold
    # Using big-M with W = hide_width, HH = hide_height
    # For each pair (p,q), if on same hide then:
    #   x_p + wp <= x_q  OR x_q + wq <= x_p  OR y_p + hp <= y_q  OR y_q + hq <= y_p
    # Since patches are fixed on a hide, we don't know which hide, but positions
    # are global. We use a "same hide" indicator = sum over h of assign[p,h]*assign[q,h].
    # Linearize: same[p,q] binary = AND of assignments (both on same hide).

    model.same = pyo.Var(model.pairs, domain=pyo.Binary)

    def same_and_rule(m, p, q):
        # same[p,q] = 1 <=> both on same hide
        # same[p,q] <= sum_h assign[p,h]*assign[q,h]  (linearized)
        # same[p,q] >= assign[p,h] + assign[q,h] - 1 for all h
        return sum(
            m.assign[p, h] + m.assign[q, h] - 1 for h in m.H
        ) >= m.same[p, q]
    # Actually easier: same[p,q] >= assign[p,h]+assign[q,h]-1 for each h
    def same_lb_rule(m, p, q, h):
        return m.same[p, q] >= m.assign[p, h] + m.assign[q, h] - 1
    model.same_lb = pyo.Constraint(model.pairs, model.H, rule=same_lb_rule)

    def same_ub_rule(m, p, q):
        return m.same[p, q] <= sum(
            m.assign[p, h] * 1 for h in m.H
        )  # trivially true; keep as bound anyway
    # Simplify: same is binary and constrained below

    # Non-overlap big-M constraints (only active if same[p,q] == 1)
    big_x = hide_width
    big_y = hide_height

    def sep_con_rule(m, p, q):
        wp = patch_widths[p]
        wq = patch_widths[q]
        hp = patch_heights[p]
        hq = patch_heights[q]
        # sum of four binaries >= same[p,q]
        # x_p + wp <= x_q + big_x*(1 - left)
        # x_q + wq <= x_p + big_x*(1 - (1-left-below-...)) ... messy
        # Use four oriented binaries with constraint sum >= 1 when same
        return pyo.Constraint.Skip
    # Implement four directional binaries explicitly

    model.dir_lr = pyo.Var(model.pairs, domain=pyo.Binary)  # p left of q
    model.dir_rl = pyo.Var(model.pairs, domain=pyo.Binary)  # q left of p
    model.dir_bt = pyo.Var(model.pairs, domain=pyo.Binary)  # p below q
    model.dir_tb = pyo.Var(model.pairs, domain=pyo.Binary)  # q below p

    def at_least_one_rule(m, p, q):
        return m.dir_lr[p, q] + m.dir_rl[p, q] + m.dir_bt[p, q] + m.dir_tb[p, q] >= m.same[p, q]
    model.atleast_con = pyo.Constraint(model.pairs, rule=at_least_one_rule)

    def lr_rule(m, p, q):
        return m.x[p] + patch_widths[p] <= m.x[q] + big_x * (1 - m.dir_lr[p, q])
    model.lr_con = pyo.Constraint(model.pairs, rule=lr_rule)

    def rl_rule(m, p, q):
        return m.x[q] + patch_widths[q] <= m.x[p] + big_x * (1 - m.dir_rl[p, q])
    model.rl_con = pyo.Constraint(model.pairs, rule=rl_rule)

    def bt_rule(m, p, q):
        return m.y[p] + patch_heights[p] <= m.y[q] + big_y * (1 - m.dir_bt[p, q])
    model.bt_con = pyo.Constraint(model.pairs, rule=bt_rule)

    def tb_rule(m, p, q):
        return m.y[q] + patch_heights[q] <= m.y[p] + big_y * (1 - m.dir_tb[p, q])
    model.tb_con = pyo.Constraint(model.pairs, rule=tb_rule)

    # Objective: minimize total hides used
    model.obj = pyo.Objective(expr=sum(model.used[h] for h in model.H), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
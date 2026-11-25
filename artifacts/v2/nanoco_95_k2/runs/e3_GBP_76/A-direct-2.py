import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    hide_w = params["hide_width"]
    hide_h = params["hide_height"]
    patch_w = list(params["patch_widths"])
    patch_h = list(params["patch_heights"])
    n = len(patch_w)

    # Upper bound on number of hides: place each patch on its own hide.
    max_hides = n

    model = pyo.ConcreteModel()

    model.PATCHES = pyo.RangeSet(0, n - 1)
    model.HIDES = pyo.RangeSet(0, max_hides - 1)

    # Assignment: does patch p go on hide h?
    model.assign = pyo.Var(model.PATCHES, model.HIDES, domain=pyo.Binary)
    # Position of patch p on its hide (lower-left corner).
    model.xpos = pyo.Var(model.PATCHES, domain=pyo.NonNegativeReals)
    model.ypos = pyo.Var(model.PATCHES, domain=pyo.NonNegativeReals)
    # Whether hide h is used.
    model.used = pyo.Var(model.HIDES, domain=pyo.Binary)

    # Each patch assigned to exactly one hide, and stays within that hide's bounds.
    model.assign_con = pyo.Constraint(
        model.PATCHES,
        rule=lambda m, p: sum(m.assign[p, h] for h in m.HIDES) == 1,
    )

    # A hide is used if any patch is assigned to it.
    model.used_con = pyo.Constraint(
        model.HIDES, model.PATCHES,
        rule=lambda m, h, p: m.used[h] >= m.assign[p, h],
    )

    # Containment: patch must fit within the hide it is assigned to.
    model.contain_x = pyo.Constraint(
        model.PATCHES,
        rule=lambda m, p: m.xpos[p] + patch_w[p]
        <= hide_w * sum(m.assign[p, h] for h in m.HIDES),
    )
    model.contain_y = pyo.Constraint(
        model.PATCHES,
        rule=lambda m, p: m.ypos[p] + patch_h[p]
        <= hide_h * sum(m.assign[p, h] for h in m.HIDES),
    )

    # Non-overlap for each pair of patches on the same hide using big-M.
    model.PAIRS = pyo.Set(
        initialize=[(i, j) for i in range(n) for j in range(i + 1, n)], dimen=2
    )
    model.left = pyo.Var(model.PAIRS, domain=pyo.Binary)   # i left of j
    model.right = pyo.Var(model.PAIRS, domain=pyo.Binary)  # i right of j
    model.above = pyo.Var(model.PAIRS, domain=pyo.Binary)  # i above j
    model.below = pyo.Var(model.PAIRS, domain=pyo.Binary)  # i below j

    Mx = hide_w + max(patch_w)
    My = hide_h + max(patch_h)

    # Separation only enforced when patches share a hide (same = 1).
    # When not on the same hide, the big-M term relaxes the constraint.
    model.sep1 = pyo.Constraint(
        model.PAIRS,
        rule=lambda m, i, j: m.xpos[i] + patch_w[i]
        <= m.xpos[j] + Mx * (2 - m.left[i, j] - sum(m.assign[i, h] * m.assign[j, h] for h in m.HIDES)),
    )
    model.sep2 = pyo.Constraint(
        model.PAIRS,
        rule=lambda m, i, j: m.xpos[j] + patch_w[j]
        <= m.xpos[i] + Mx * (2 - m.right[i, j] - sum(m.assign[i, h] * m.assign[j, h] for h in m.HIDES)),
    )
    model.sep3 = pyo.Constraint(
        model.PAIRS,
        rule=lambda m, i, j: m.ypos[i] + patch_h[i]
        <= m.ypos[j] + My * (2 - m.above[i, j] - sum(m.assign[i, h] * m.assign[j, h] for h in m.HIDES)),
    )
    model.sep4 = pyo.Constraint(
        model.PAIRS,
        rule=lambda m, i, j: m.ypos[j] + patch_h[j]
        <= m.ypos[i] + My * (2 - m.below[i, j] - sum(m.assign[i, h] * m.assign[j, h] for h in m.HIDES)),
    )

    # At least one separation direction active per same-hide pair.
    model.sep_dir = pyo.Constraint(
        model.PAIRS,
        rule=lambda m, i, j: m.left[i, j] + m.right[i, j] + m.above[i, j] + m.below[i, j]
        >= sum(m.assign[i, h] * m.assign[j, h] for h in m.HIDES),
    )

    # Symmetry breaking: hide usage is prefix-ordered.
    def prefix_rule(m, h):
        if h == m.HIDES.first():
            return pyo.Constraint.Skip
        return m.used[h] <= m.used[h - 1]
    model.prefix_con = pyo.Constraint(model.HIDES, rule=prefix_rule)

    # Objective: minimize number of hides used.
    model.total_hides = pyo.Objective(
        rule=lambda m: sum(m.used[h] for h in m.HIDES), sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_hides))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hide_w = params["hide_width"]
    hide_h = params["hide_height"]
    widths = params["patch_widths"]
    heights = params["patch_heights"]

    n_patches = len(widths)
    n_hides = n_patches  # worst case: one patch per hide

    patches = range(n_patches)
    hides = range(n_hides)

    model = pyo.ConcreteModel()

    # Number of hides used (linearization of the max hide index used)
    model.num_hides = pyo.Var(domain=pyo.NonNegativeReals)

    # Binary: which hide is actually used
    model.used = pyo.Var(hides, domain=pyo.Binary)

    # Assignment: patch i assigned to hide k
    model.assign = pyo.Var(patches, hides, domain=pyo.Binary)

    # Position of patch i
    model.x = pyo.Var(patches, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(patches, domain=pyo.NonNegativeReals)

    # Relative position binaries for overlap avoidance (pairwise, if same hide)
    pairs = [(i, j) for i in patches for j in patches if i < j]
    model.left = pyo.Var(pairs, domain=pyo.Binary)
    model.right = pyo.Var(pairs, domain=pyo.Binary)
    model.below = pyo.Var(pairs, domain=pyo.Binary)
    model.above = pyo.Var(pairs, domain=pyo.Binary)

    # Each patch assigned exactly once
    model.assign_once = pyo.Constraint(
        patches, rule=lambda m, i: sum(m.assign[i, k] for k in hides) == 1
    )

    # Bounds: containment within hide (in absolute coordinates, relative to hide origin)
    # We use hide-local coordinates; each patch must fit within hide width/height.
    model.fit_w = pyo.Constraint(
        patches, rule=lambda m, i: m.x[i] + widths[i] <= hide_w
    )
    model.fit_h = pyo.Constraint(
        patches, rule=lambda m, i: m.y[i] + heights[i] <= hide_h
    )

    # Link: if patch i on hide k, hide k must be used
    model.use_link = pyo.Constraint(
        patches, hides,
        rule=lambda m, i, k: m.assign[i, k] <= m.used[k]
    )

    # num_hides >= sum(used) is trivial; instead minimize sum(used)
    model.num_hides_def = pyo.Constraint(
        expr=model.num_hides == sum(model.used[k] for k in hides)
    )

    # Non-overlap: for each pair of patches that might share a hide,
    # enforce separation along x or y. We use global coordinates (hide-local merged).
    # To handle cross-hide separation, we offset by hide index so cross-hide patches never conflict,
    # but the cleanest approach: enforce that if on same hide, one of the four orderings holds.
    def overlap_rule(m, i, j):
        # same_hide binary
        same = pyo.Quo  # placeholder not used
        return pyo.Constraint.Skip

    # Big-M
    big_m_width = hide_w + max(widths) + hide_w * n_hides
    big_m_height = hide_h + max(heights) + hide_h * n_hides

    # We enforce non-overlap conditional on same hide using assignment product.
    # Introduce same_hide indicator via linearization using sum over hides of min? 
    # Simpler: enforce four disjunctions with big-M AND require that cross-hide pairs are separated by hide slot.
    # We'll place patches in "global" coordinates: x[i] in [0, n_hides*hide_w], patch assigned to hide h occupies [h*hide_w, h*hide_w+hide_w].
    # Redefine x bounds per hide via assignment linking.
    model.x_global = pyo.Var(patches, domain=pyo.NonNegativeReals)
    model.y_global = pyo.Var(patches, domain=pyo.NonNegativeReals)

    for i in patches:
        model.x_global[i].setub(n_hides * hide_w)
        model.y_global[i].setub(n_hides * hide_h)

    # Patch i within hide k: if assigned, h*hide_w <= x_global <= (h+1)*hide_w - width
    def assign_x_lb(m, i, k):
        return m.x_global[i] >= k * hide_w * m.assign[i, k]

    def assign_x_ub(m, i, k):
        return m.x_global[i] + widths[i] <= m.assign[i, k] * (k + 1) * hide_w + (1 - m.assign[i, k]) * n_hides * hide_w

    def assign_y_lb(m, i, k):
        return m.y_global[i] >= k * hide_h * m.assign[i, k]

    def assign_y_ub(m, i, k):
        return m.y_global[i] + heights[i] <= m.assign[i, k] * (k + 1) * hide_h + (1 - m.assign[i, k]) * n_hides * hide_h

    model.ax_lb = pyo.Constraint(patches, hides, rule=assign_x_lb)
    model.ax_ub = pyo.Constraint(patches, hides, rule=assign_x_ub)
    model.ay_lb = pyo.Constraint(patches, hides, rule=assign_y_lb)
    model.ay_ub = pyo.Constraint(patches, hides, rule=assign_y_ub)

    def x_span(m, i):
        return m.x_global[i] <= n_hides * hide_w

    # Non-overlap on global coordinates with 4-way disjunction (big-M)
    def pair_rule(m, i, j):
        # x_i + w_i <= x_j OR x_j + w_j <= x_i OR y_i + h_i <= y_j OR y_j + h_j <= y_i
        return (m.left[i, j] + m.right[i, j] + m.below[i, j] + m.above[i, j] >= 1)

    model.disj_sum = pyo.Constraint(pairs, rule=pair_rule)

    def left_rule(m, i, j):
        return m.x_global[i] + widths[i] <= m.x_global[j] + (1 - m.left[i, j]) * (n_hides * hide_w + max(widths))

    def right_rule(m, i, j):
        return m.x_global[j] + widths[j] <= m.x_global[i] + (1 - m.right[i, j]) * (n_hides * hide_w + max(widths))

    def below_rule(m, i, j):
        return m.y_global[i] + heights[i] <= m.y_global[j] + (1 - m.below[i, j]) * (n_hides * hide_h + max(heights))

    def above_rule(m, i, j):
        return m.y_global[j] + heights[j] <= m.y_global[i] + (1 - m.above[i, j]) * (n_hides * hide_h + max(heights))

    model.left_c = pyo.Constraint(pairs, rule=left_rule)
    model.right_c = pyo.Constraint(pairs, rule=right_rule)
    model.below_c = pyo.Constraint(pairs, rule=below_rule)
    model.above_c = pyo.Constraint(pairs, rule=above_rule)

    model.obj = pyo.Objective(expr=model.num_hides, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}
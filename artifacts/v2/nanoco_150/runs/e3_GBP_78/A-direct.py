import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    frame_width = params["frame_width"]
    frame_height = params["frame_height"]
    array_widths = params["array_widths"]
    array_heights = params["array_heights"]

    n = len(array_widths)
    arrays = list(range(n))
    frames = list(range(n))

    model = pyo.ConcreteModel()

    model.ARRAYS = pyo.Set(initialize=arrays)
    model.FRAMES = pyo.Set(initialize=frames)
    model.PAIR_LIST = [(i, j) for i in arrays for j in arrays if i < j]
    model.PAIRS = pyo.Set(initialize=model.PAIR_LIST, dimen=2)

    model.assign = pyo.Var(model.ARRAYS, model.FRAMES, domain=pyo.Binary)
    model.x = pyo.Var(model.ARRAYS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.ARRAYS, domain=pyo.NonNegativeReals)
    model.used = pyo.Var(model.FRAMES, domain=pyo.Binary)

    # same[f,i,j] = 1 iff arrays i and j are both assigned to frame f
    model.same = pyo.Var(model.FRAMES, model.PAIRS, domain=pyo.Binary)

    # disjunctive indicators per pair
    model.lr = pyo.Var(model.PAIRS, domain=pyo.Binary)
    model.rl = pyo.Var(model.PAIRS, domain=pyo.Binary)
    model.ab = pyo.Var(model.PAIRS, domain=pyo.Binary)
    model.ba = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def objective_rule(m):
        return sum(m.used[f] for f in m.FRAMES)

    model.total_frames = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def assign_once_rule(m, i):
        return sum(m.assign[i, f] for f in m.FRAMES) == 1

    model.assign_once = pyo.Constraint(model.ARRAYS, rule=assign_once_rule)

    def used_link_rule(m, i, f):
        return m.used[f] >= m.assign[i, f]

    model.used_link = pyo.Constraint(model.ARRAYS, model.FRAMES, rule=used_link_rule)

    def width_fit_rule(m, i):
        return m.x[i] + array_widths[i] <= frame_width

    def height_fit_rule(m, i):
        return m.y[i] + array_heights[i] <= frame_height

    model.width_fit = pyo.Constraint(model.ARRAYS, rule=width_fit_rule)
    model.height_fit = pyo.Constraint(model.ARRAYS, rule=height_fit_rule)

    # Linear big-M linking for same-frame indicator
    def same_upper_rule(m, f, i, j):
        return m.same[f, i, j] <= m.assign[i, f]

    def same_upper2_rule(m, f, i, j):
        return m.same[f, i, j] <= m.assign[j, f]

    def same_lower_rule(m, f, i, j):
        return m.same[f, i, j] >= m.assign[i, f] + m.assign[j, f] - 1

    model.same_upper = pyo.Constraint(model.FRAMES, model.PAIRS, rule=same_upper_rule)
    model.same_upper2 = pyo.Constraint(model.FRAMES, model.PAIRS, rule=same_upper2_rule)
    model.same_lower = pyo.Constraint(model.FRAMES, model.PAIRS, rule=same_lower_rule)

    # disjunction must be satisfied if arrays share any frame
    def disj_rule(m, i, j):
        shared = sum(m.same[f, i, j] for f in m.FRAMES)
        return m.lr[i, j] + m.rl[i, j] + m.ab[i, j] + m.ba[i, j] >= shared

    model.disj_sum = pyo.Constraint(model.PAIRS, rule=disj_rule)

    def bigm_lr_rule(m, i, j):
        shared = sum(m.same[f, i, j] for f in m.FRAMES)
        return m.x[i] + array_widths[i] <= m.x[j] + frame_width * (1 - shared) + frame_width * (1 - m.lr[i, j])

    def bigm_rl_rule(m, i, j):
        shared = sum(m.same[f, i, j] for f in m.FRAMES)
        return m.x[j] + array_widths[j] <= m.x[i] + frame_width * (1 - shared) + frame_width * (1 - m.rl[i, j])

    def bigm_ab_rule(m, i, j):
        shared = sum(m.same[f, i, j] for f in m.FRAMES)
        return m.y[i] + array_heights[i] <= m.y[j] + frame_height * (1 - shared) + frame_height * (1 - m.ab[i, j])

    def bigm_ba_rule(m, i, j):
        shared = sum(m.same[f, i, j] for f in m.FRAMES)
        return m.y[j] + array_heights[j] <= m.y[i] + frame_height * (1 - shared) + frame_height * (1 - m.ba[i, j])

    model.bigm_lr = pyo.Constraint(model.PAIRS, rule=bigm_lr_rule)
    model.bigm_rl = pyo.Constraint(model.PAIRS, rule=bigm_rl_rule)
    model.bigm_ab = pyo.Constraint(model.PAIRS, rule=bigm_ab_rule)
    model.bigm_ba = pyo.Constraint(model.PAIRS, rule=bigm_ba_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_frames))
    return {"objective": obj_val, "status": "optimal"}
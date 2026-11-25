import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    target_times = params["target_times"]
    earliest_times = params["earliest_times"]
    latest_times = params["latest_times"]
    early_penalties = params["early_penalties"]
    late_penalties = params["late_penalties"]

    sep = {
        (0, 1): params["separation_0_1"],
        (0, 2): params["separation_0_2"],
        (0, 3): params["separation_0_3"],
        (1, 2): params["separation_1_2"],
        (1, 3): params["separation_1_3"],
        (2, 3): params["separation_2_3"],
    }

    def separation(i, j):
        if (i, j) in sep:
            return sep[(i, j)]
        return sep[(j, i)]

    aircraft = list(range(4))
    pairs = [(i, j) for i in aircraft for j in aircraft if i < j]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.t = pyo.Var(model.A, within=pyo.Reals)
    model.early = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.late = pyo.Var(model.A, within=pyo.NonNegativeReals)
    model.z = pyo.Var(model.P, within=pyo.Binary)

    def time_bounds_rule(m, i):
        return (earliest_times[i], latest_times[i])
    model.time_bounds = pyo.Constraint(model.A, rule=time_bounds_rule)

    def dev_early_rule(m, i):
        return m.t[i] - target_times[i] >= -m.early[i]
    model.dev_early = pyo.Constraint(model.A, rule=dev_early_rule)

    def dev_late_rule(m, i):
        return m.t[i] - target_times[i] <= m.late[i]
    model.dev_late = pyo.Constraint(model.A, rule=dev_late_rule)

    def sep_rule(m, i, j):
        # z == 1 => i before j; z == 0 => j before i
        s_ij = separation(i, j)
        s_ji = separation(j, i)
        M_ij = latest_times[j] - earliest_times[i]
        return m.t[j] - m.t[i] >= s_ij * m.z[(i, j)] - M_ij * (1 - m.z[(i, j)])
    model.sep_pairs = pyo.Constraint(model.P, rule=sep_rule)

    def sep_reverse_rule(m, i, j):
        s_ji = separation(j, i)
        M_ji = latest_times[i] - earliest_times[j]
        return m.t[i] - m.t[j] >= s_ji * (1 - m.z[(i, j)]) - M_ji * m.z[(i, j)]
    model.sep_pairs_rev = pyo.Constraint(model.P, rule=sep_reverse_rule)

    def obj_rule(m):
        return sum(
            early_penalties[i] * m.early[i] + late_penalties[i] * m.late[i]
            for i in m.A
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
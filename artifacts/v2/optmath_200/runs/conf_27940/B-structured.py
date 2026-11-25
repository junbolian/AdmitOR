# IR: {"sets":{"A":[0,1,2,3],"P":[[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]]},"params":{"target_times":"indexed by A","earliest_times":"indexed by A","latest_times":"indexed by A","early_penalties":"indexed by A","late_penalties":"indexed by A","separation_0_1":"scalar","separation_0_2":"scalar","separation_0_3":"scalar","separation_1_2":"scalar","separation_1_3":"scalar","separation_2_3":"scalar"},"derived":{"s[i,j]":"separation_i_j","M_forward[i,j]":"max(0,latest_times[i]+s[i,j]-earliest_times[j])","M_reverse[i,j]":"max(0,latest_times[j]+s[i,j]-earliest_times[i])"},"variables":{"landing[i]":"real, earliest_times[i] <= landing[i] <= latest_times[i]","early[i]":"nonnegative real","late[i]":"nonnegative real","before[i,j]":"binary; 1 means i precedes j"},"constraints":["landing[i]+early[i]-late[i]=target_times[i] for i in A","landing[j]-landing[i]>=s[i,j]-M_forward[i,j]*(1-before[i,j]) for (i,j) in P","landing[i]-landing[j]>=s[i,j]-M_reverse[i,j]*before[i,j] for (i,j) in P"],"objective":"minimize sum(early_penalties[i]*early[i]+late_penalties[i]*late[i] for i in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = range(4)
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    target = params["target_times"]
    earliest = params["earliest_times"]
    latest = params["latest_times"]
    early_cost = params["early_penalties"]
    late_cost = params["late_penalties"]

    separation = {
        (0, 1): params["separation_0_1"],
        (0, 2): params["separation_0_2"],
        (0, 3): params["separation_0_3"],
        (1, 2): params["separation_1_2"],
        (1, 3): params["separation_1_3"],
        (2, 3): params["separation_2_3"],
    }
    big_forward = {
        (i, j): max(0, latest[i] + separation[i, j] - earliest[j])
        for i, j in pairs
    }
    big_reverse = {
        (i, j): max(0, latest[j] + separation[i, j] - earliest[i])
        for i, j in pairs
    }

    model = pyo.ConcreteModel()
    model.aircraft = pyo.Set(initialize=aircraft, ordered=True)
    model.pairs = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.landing = pyo.Var(
        model.aircraft,
        domain=pyo.Reals,
        bounds=lambda mdl, i: (earliest[i], latest[i]),
    )
    model.early = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)
    model.late = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)
    model.before = pyo.Var(model.pairs, domain=pyo.Binary)

    def deviation_rule(mdl, i):
        return mdl.landing[i] + mdl.early[i] - mdl.late[i] == target[i]

    model.deviation = pyo.Constraint(model.aircraft, rule=deviation_rule)

    def forward_rule(mdl, i, j):
        return (
            mdl.landing[j] - mdl.landing[i]
            >= separation[i, j] - big_forward[i, j] * (1 - mdl.before[i, j])
        )

    model.forward_separation = pyo.Constraint(model.pairs, rule=forward_rule)

    def reverse_rule(mdl, i, j):
        return (
            mdl.landing[i] - mdl.landing[j]
            >= separation[i, j] - big_reverse[i, j] * mdl.before[i, j]
        )

    model.reverse_separation = pyo.Constraint(model.pairs, rule=reverse_rule)

    model.total_penalty = pyo.Objective(
        expr=sum(
            early_cost[i] * model.early[i] + late_cost[i] * model.late[i]
            for i in model.aircraft
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_penalty))
    except (ValueError, TypeError, RuntimeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"A":[0,1,2,3,4],"P":"{(i,j): i,j in A, i<j}"},"params":{"earliest[i]":"params[earliest_i]","latest[i]":"params[latest_i]","target[i]":"params[target_i]","early_cost[i]":"params[early_cost_i]","late_cost[i]":"params[late_cost_i]","sep[i,j]":"params[sep_i_j]","M_forward[i,j]":"max(0,latest[i]+sep[i,j]-earliest[j])","M_reverse[i,j]":"max(0,latest[j]+sep[i,j]-earliest[i])"},"variables":{"landing[i]":"continuous, earliest[i]<=landing[i]<=latest[i]","early[i]":"continuous, nonnegative","late[i]":"continuous, nonnegative","precedes[i,j]":"binary; 1 means i lands before j"},"constraints":["landing[i]-target[i]=late[i]-early[i] for i in A","landing[j]>=landing[i]+sep[i,j]-M_forward[i,j]*(1-precedes[i,j]) for (i,j) in P","landing[i]>=landing[j]+sep[i,j]-M_reverse[i,j]*precedes[i,j] for (i,j) in P"],"objective":"minimize sum(early_cost[i]*early[i]+late_cost[i]*late[i] for i in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = tuple(range(5))
    pairs = tuple(
        (i, j) for i in aircraft for j in aircraft if i < j
    )

    earliest = {i: params[f"earliest_{i}"] for i in aircraft}
    latest = {i: params[f"latest_{i}"] for i in aircraft}
    target = {i: params[f"target_{i}"] for i in aircraft}
    early_cost = {i: params[f"early_cost_{i}"] for i in aircraft}
    late_cost = {i: params[f"late_cost_{i}"] for i in aircraft}
    separation = {
        (i, j): params[f"sep_{i}_{j}"] for i, j in pairs
    }

    big_m_forward = {
        (i, j): max(0, latest[i] + separation[i, j] - earliest[j])
        for i, j in pairs
    }
    big_m_reverse = {
        (i, j): max(0, latest[j] + separation[i, j] - earliest[i])
        for i, j in pairs
    }

    model = pyo.ConcreteModel()
    model.aircraft = pyo.Set(initialize=aircraft, ordered=True)
    model.pairs = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.earliest = pyo.Param(model.aircraft, initialize=earliest)
    model.latest = pyo.Param(model.aircraft, initialize=latest)
    model.target = pyo.Param(model.aircraft, initialize=target)
    model.early_cost = pyo.Param(model.aircraft, initialize=early_cost)
    model.late_cost = pyo.Param(model.aircraft, initialize=late_cost)
    model.separation = pyo.Param(model.pairs, initialize=separation)
    model.big_m_forward = pyo.Param(
        model.pairs, initialize=big_m_forward
    )
    model.big_m_reverse = pyo.Param(
        model.pairs, initialize=big_m_reverse
    )

    def landing_bounds(instance, i):
        return (
            pyo.value(instance.earliest[i]),
            pyo.value(instance.latest[i]),
        )

    model.landing = pyo.Var(
        model.aircraft, domain=pyo.Reals, bounds=landing_bounds
    )
    model.early = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)
    model.late = pyo.Var(model.aircraft, domain=pyo.NonNegativeReals)
    model.precedes = pyo.Var(model.pairs, domain=pyo.Binary)

    def deviation_rule(instance, i):
        return (
            instance.landing[i] - instance.target[i]
            == instance.late[i] - instance.early[i]
        )

    model.deviation_balance = pyo.Constraint(
        model.aircraft, rule=deviation_rule
    )

    def forward_separation_rule(instance, i, j):
        return instance.landing[j] >= (
            instance.landing[i]
            + instance.separation[i, j]
            - instance.big_m_forward[i, j]
            * (1 - instance.precedes[i, j])
        )

    model.forward_separation = pyo.Constraint(
        model.pairs, rule=forward_separation_rule
    )

    def reverse_separation_rule(instance, i, j):
        return instance.landing[i] >= (
            instance.landing[j]
            + instance.separation[i, j]
            - instance.big_m_reverse[i, j] * instance.precedes[i, j]
        )

    model.reverse_separation = pyo.Constraint(
        model.pairs, rule=reverse_separation_rule
    )

    model.total_penalty = pyo.Objective(
        expr=sum(
            model.early_cost[i] * model.early[i]
            + model.late_cost[i] * model.late[i]
            for i in model.aircraft
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_penalty))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
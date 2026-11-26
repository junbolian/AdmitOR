# IR: {"sets":{"T":"1..n","S":"{t in T: t+p<=n}","F":"{t in T: t+q<=n}"},"params":{"a":"params['a']","b":"params['b']","c":"params['c']","p":"params['p']","q":"params['q']","r":"params['r']; index 0 unused","n":"params['n']"},"variables":{"buy[t in T]":"nonnegative integer","slow[t in S]":"nonnegative integer","fast[t in F]":"nonnegative integer","stock[t in T]":"nonnegative integer; usable tools remaining after stage t"},"constraints":["For each t in T: stock[t] = (stock[t-1] if t>1 else 0) + buy[t] + (slow[t-p] if t-p in S else 0) + (fast[t-q] if t-q in F else 0) - r[t].","For each t in T: (slow[t] if t in S else 0) + (fast[t] if t in F else 0) <= r[t]; unassigned used tools are retired."],"objective":"minimize a*sum(buy[t] for t in T) + b*sum(slow[t] for t in S) + c*sum(fast[t] for t in F)","timing":"Tools used in stage t and repaired with duration d return at the start of stage t+d."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]
    c = params["c"]
    p = params["p"]
    q = params["q"]
    r = params["r"]
    n = params["n"]

    model = pyo.ConcreteModel()

    model.stages = pyo.RangeSet(1, n)
    model.slow_stages = pyo.Set(
        initialize=[stage for stage in model.stages if stage + p <= n],
        within=model.stages,
    )
    model.fast_stages = pyo.Set(
        initialize=[stage for stage in model.stages if stage + q <= n],
        within=model.stages,
    )

    model.buy = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)
    model.slow = pyo.Var(model.slow_stages, domain=pyo.NonNegativeIntegers)
    model.fast = pyo.Var(model.fast_stages, domain=pyo.NonNegativeIntegers)
    model.stock = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)

    def inventory_balance_rule(model, stage):
        previous_stock = model.stock[stage - 1] if stage > 1 else 0
        slow_returns = (
            model.slow[stage - p] if stage - p in model.slow_stages else 0
        )
        fast_returns = (
            model.fast[stage - q] if stage - q in model.fast_stages else 0
        )
        return model.stock[stage] == (
            previous_stock
            + model.buy[stage]
            + slow_returns
            + fast_returns
            - r[stage]
        )

    model.inventory_balance = pyo.Constraint(
        model.stages, rule=inventory_balance_rule
    )

    def repair_capacity_rule(model, stage):
        slow_dispatch = model.slow[stage] if stage in model.slow_stages else 0
        fast_dispatch = model.fast[stage] if stage in model.fast_stages else 0
        if stage not in model.slow_stages and stage not in model.fast_stages:
            return pyo.Constraint.Feasible
        return slow_dispatch + fast_dispatch <= r[stage]

    model.repair_capacity = pyo.Constraint(
        model.stages, rule=repair_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            a * sum(model.buy[stage] for stage in model.stages)
            + b * sum(model.slow[stage] for stage in model.slow_stages)
            + c * sum(model.fast[stage] for stage in model.fast_stages)
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
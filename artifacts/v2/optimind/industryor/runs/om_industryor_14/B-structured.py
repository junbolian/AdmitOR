# IR: {"sets":{"T":"1..n","n":"len(params['r'])"},"params":{"a":"params['a']","b":"params['b']","c":"params['c']","p":"params['p'], positive integer","q":"params['q'], positive integer","r[j]":"params['r'][j-1], nonnegative integer"},"variables":{"purchase[j]":"nonnegative integer","slow[j]":"nonnegative integer, sent after stage j","fast[j]":"nonnegative integer, sent after stage j","inventory[j]":"nonnegative integer, unused serviceable tools after stage j"},"constraints":["slow[j]+fast[j]=r[j] for every j","inventory[j]=inventory[j-1]+purchase[j]+slow[j-p]+fast[j-q]-r[j] for every j; inventory[0]=0 and nonpositive-index repair terms are zero"],"objective":"minimize sum(a*purchase[j]+b*slow[j]+c*fast[j] for j in T)","horizon":"All used tools are sent for repair as required, including at the final stage; repair costs are charged when dispatched, even if return occurs after n."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]
    c = params["c"]
    p_input = params["p"]
    q_input = params["q"]
    requirements = list(params["r"])

    p = int(p_input)
    q = int(q_input)

    if p != p_input or q != q_input or not (0 < q < p):
        return {"objective": None, "status": "invalid_lead_times"}

    if not (0 <= b < c < a):
        return {"objective": None, "status": "invalid_costs"}

    if any(value < 0 or int(value) != value for value in requirements):
        return {"objective": None, "status": "invalid_requirements"}

    n = len(requirements)

    model = pyo.ConcreteModel()
    model.stages = pyo.Set(initialize=range(1, n + 1), ordered=True)

    model.purchase_cost = pyo.Param(initialize=a, within=pyo.NonNegativeReals)
    model.slow_cost = pyo.Param(initialize=b, within=pyo.NonNegativeReals)
    model.fast_cost = pyo.Param(initialize=c, within=pyo.NonNegativeReals)
    model.slow_lead = pyo.Param(initialize=p, within=pyo.PositiveIntegers)
    model.fast_lead = pyo.Param(initialize=q, within=pyo.PositiveIntegers)
    model.requirement = pyo.Param(
        model.stages,
        initialize={
            stage: requirements[stage - 1]
            for stage in range(1, n + 1)
        },
        within=pyo.NonNegativeIntegers,
    )

    model.purchase = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)
    model.slow = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)
    model.fast = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)
    model.inventory = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)

    def repair_dispatch_rule(instance, stage):
        return (
            instance.slow[stage] + instance.fast[stage]
            == instance.requirement[stage]
        )

    model.repair_dispatch = pyo.Constraint(
        model.stages, rule=repair_dispatch_rule
    )

    def inventory_balance_rule(instance, stage):
        previous_inventory = (
            instance.inventory[stage - 1] if stage > 1 else 0
        )
        slow_returns = (
            instance.slow[stage - p] if stage > p else 0
        )
        fast_returns = (
            instance.fast[stage - q] if stage > q else 0
        )
        return instance.inventory[stage] == (
            previous_inventory
            + instance.purchase[stage]
            + slow_returns
            + fast_returns
            - instance.requirement[stage]
        )

    model.inventory_balance = pyo.Constraint(
        model.stages, rule=inventory_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            (
                model.purchase_cost * model.purchase[stage]
                + model.slow_cost * model.slow[stage]
                + model.fast_cost * model.fast[stage]
            )
            for stage in model.stages
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
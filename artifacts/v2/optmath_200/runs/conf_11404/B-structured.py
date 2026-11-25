# IR: {"sets":{"candidates":[0,1,2,3,4,5,6,7,8,9,10,11,12]},"params":{"value[i]":"params['value_'+str(i)]","cost[i]":"params['cost_'+str(i)]","budget":"params['budget']"},"variables":{"hire[i]":"Binary"},"constraints":["sum(cost[i]*hire[i] for i in candidates) <= budget"],"objective":{"sense":"maximize","expression":"sum(value[i]*hire[i] for i in candidates)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.candidates = pyo.RangeSet(0, 12)

    model.candidate_value = pyo.Param(
        model.candidates,
        initialize={
            idx: params[f"value_{idx}"] for idx in model.candidates
        },
        within=pyo.Reals,
    )
    model.candidate_cost = pyo.Param(
        model.candidates,
        initialize={
            idx: params[f"cost_{idx}"] for idx in model.candidates
        },
        within=pyo.Reals,
    )
    model.hiring_budget = pyo.Param(
        initialize=params["budget"],
        within=pyo.Reals,
    )

    model.hire = pyo.Var(model.candidates, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.candidate_cost[idx] * model.hire[idx]
            for idx in model.candidates
        ) <= model.hiring_budget
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.candidate_value[idx] * model.hire[idx]
            for idx in model.candidates
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
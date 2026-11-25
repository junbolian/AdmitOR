# IR: {"sets":{"I":"0..10"},"params":{"value":"value[i], i in I","salary":"salary[i], i in I","budget":"total salary budget"},"variables":{"hire[i]":"Binary, i in I"},"constraints":["sum(salary[i]*hire[i] for i in I) <= budget"],"objective":"maximize sum(value[i]*hire[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.candidates = pyo.RangeSet(0, 10)

    model.candidate_value = pyo.Param(
        model.candidates,
        initialize={i: params["value"][i] for i in model.candidates},
        within=pyo.Reals,
    )
    model.candidate_salary = pyo.Param(
        model.candidates,
        initialize={i: params["salary"][i] for i in model.candidates},
        within=pyo.Reals,
    )
    model.salary_budget = pyo.Param(
        initialize=params["budget"],
        within=pyo.Reals,
    )

    model.hire = pyo.Var(model.candidates, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.candidate_salary[i] * model.hire[i]
            for i in model.candidates
        ) <= model.salary_budget
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.candidate_value[i] * model.hire[i]
            for i in model.candidates
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
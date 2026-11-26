# IR: {"sets":{"I":[1,2,3,4,5]},"params":{"time0_outflow":"length-5 sequence","time1_outflow":"length-5 sequence","npv":"length-5 sequence","budget_time0":"scalar","budget_time1":"scalar"},"variables":{"fraction[i]":"continuous, 0 <= fraction[i] <= 1"},"constraints":["sum(time0_outflow[i]*fraction[i] for i in I) <= budget_time0","sum(time1_outflow[i]*fraction[i] for i in I) <= budget_time1"],"objective":"maximize sum(npv[i]*fraction[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Input sequences list investments 1 through 5 in that order."""
    time0_outflow = params["time0_outflow"]
    time1_outflow = params["time1_outflow"]
    npv = params["npv"]
    budget_time0 = params["budget_time0"]
    budget_time1 = params["budget_time1"]

    model = pyo.ConcreteModel()
    model.investments = pyo.RangeSet(1, 5)

    model.cost_time0 = pyo.Param(
        model.investments,
        initialize={i: time0_outflow[i - 1] for i in model.investments},
    )
    model.cost_time1 = pyo.Param(
        model.investments,
        initialize={i: time1_outflow[i - 1] for i in model.investments},
    )
    model.value_npv = pyo.Param(
        model.investments,
        initialize={i: npv[i - 1] for i in model.investments},
    )
    model.funds_time0 = pyo.Param(initialize=budget_time0)
    model.funds_time1 = pyo.Param(initialize=budget_time1)

    model.fraction = pyo.Var(
        model.investments,
        domain=pyo.NonNegativeReals,
        bounds=(0, 1),
    )

    model.budget_constraint_time0 = pyo.Constraint(
        expr=sum(
            model.cost_time0[i] * model.fraction[i]
            for i in model.investments
        ) <= model.funds_time0
    )
    model.budget_constraint_time1 = pyo.Constraint(
        expr=sum(
            model.cost_time1[i] * model.fraction[i]
            for i in model.investments
        ) <= model.funds_time1
    )
    model.total_npv = pyo.Objective(
        expr=sum(
            model.value_npv[i] * model.fraction[i]
            for i in model.investments
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this error when it cannot load a feasible solution.
        # Leave success determination to objective evaluation below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_npv))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
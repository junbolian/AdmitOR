# IR: {"sets":{"I":[0,1,2,3,4]},"params":{"time0_outflow":"length-5 array indexed by I","time1_outflow":"length-5 array indexed by I","npv":"length-5 array indexed by I","budget_time0":"scalar","budget_time1":"scalar"},"variables":{"x[i]":"continuous, 0 <= x[i] <= 1; fraction of investment i+1 purchased"},"constraints":["sum(time0_outflow[i]*x[i] for i in I) <= budget_time0","sum(time1_outflow[i]*x[i] for i in I) <= budget_time1"],"objective":"maximize sum(npv[i]*x[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.investments = pyo.RangeSet(0, 4)

    model.time0_outflow = pyo.Param(
        model.investments,
        initialize={
            i: params["time0_outflow"][i] for i in model.investments
        },
        within=pyo.NonNegativeReals,
    )
    model.time1_outflow = pyo.Param(
        model.investments,
        initialize={
            i: params["time1_outflow"][i] for i in model.investments
        },
        within=pyo.NonNegativeReals,
    )
    model.npv = pyo.Param(
        model.investments,
        initialize={i: params["npv"][i] for i in model.investments},
        within=pyo.Reals,
    )
    model.budget_time0 = pyo.Param(
        initialize=params["budget_time0"],
        within=pyo.NonNegativeReals,
    )
    model.budget_time1 = pyo.Param(
        initialize=params["budget_time1"],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.investments, domain=pyo.UnitInterval)

    model.time0_budget_constraint = pyo.Constraint(
        expr=sum(
            model.time0_outflow[i] * model.x[i]
            for i in model.investments
        ) <= model.budget_time0
    )
    model.time1_budget_constraint = pyo.Constraint(
        expr=sum(
            model.time1_outflow[i] * model.x[i]
            for i in model.investments
        ) <= model.budget_time1
    )

    model.total_npv = pyo.Objective(
        expr=sum(model.npv[i] * model.x[i] for i in model.investments),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_npv))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
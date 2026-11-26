# IR: {"sets":{"years":[1,2,3]},"params":["initial_fund","return_rate_project1","return_multiplier_project2","cap_project2","return_multiplier_project3","cap_project3","return_multiplier_project4","cap_project4"],"variables":{"investment1[years]":"nonnegative continuous","investment2":"nonnegative continuous","investment3":"nonnegative continuous","investment4":"nonnegative continuous","cash[years]":"nonnegative continuous"},"constraints":["investment1[1]+investment2+cash[1]=initial_fund","investment1[2]+investment3+cash[2]=(1+return_rate_project1)*investment1[1]+cash[1]","investment1[3]+investment4+cash[3]=(1+return_rate_project1)*investment1[2]+return_multiplier_project2*investment2+cash[2]","investment2<=cap_project2","investment3<=cap_project3","investment4<=cap_project4"],"objective":"maximize (1+return_rate_project1)*investment1[3]+return_multiplier_project3*investment3+return_multiplier_project4*investment4+cash[3]"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.years = pyo.RangeSet(1, 3)

    model.initial_fund = pyo.Param(initialize=params["initial_fund"])
    model.return_rate_project1 = pyo.Param(
        initialize=params["return_rate_project1"]
    )
    model.return_multiplier_project2 = pyo.Param(
        initialize=params["return_multiplier_project2"]
    )
    model.cap_project2 = pyo.Param(initialize=params["cap_project2"])
    model.return_multiplier_project3 = pyo.Param(
        initialize=params["return_multiplier_project3"]
    )
    model.cap_project3 = pyo.Param(initialize=params["cap_project3"])
    model.return_multiplier_project4 = pyo.Param(
        initialize=params["return_multiplier_project4"]
    )
    model.cap_project4 = pyo.Param(initialize=params["cap_project4"])

    model.investment1 = pyo.Var(model.years, domain=pyo.NonNegativeReals)
    model.investment2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.investment3 = pyo.Var(domain=pyo.NonNegativeReals)
    model.investment4 = pyo.Var(domain=pyo.NonNegativeReals)
    model.cash = pyo.Var(model.years, domain=pyo.NonNegativeReals)

    model.year1_balance = pyo.Constraint(
        expr=model.investment1[1] + model.investment2 + model.cash[1]
        == model.initial_fund
    )
    model.year2_balance = pyo.Constraint(
        expr=model.investment1[2] + model.investment3 + model.cash[2]
        == (1 + model.return_rate_project1) * model.investment1[1]
        + model.cash[1]
    )
    model.year3_balance = pyo.Constraint(
        expr=model.investment1[3] + model.investment4 + model.cash[3]
        == (1 + model.return_rate_project1) * model.investment1[2]
        + model.return_multiplier_project2 * model.investment2
        + model.cash[2]
    )

    model.project2_limit = pyo.Constraint(
        expr=model.investment2 <= model.cap_project2
    )
    model.project3_limit = pyo.Constraint(
        expr=model.investment3 <= model.cap_project3
    )
    model.project4_limit = pyo.Constraint(
        expr=model.investment4 <= model.cap_project4
    )

    model.terminal_wealth = pyo.Objective(
        expr=(1 + model.return_rate_project1) * model.investment1[3]
        + model.return_multiplier_project3 * model.investment3
        + model.return_multiplier_project4 * model.investment4
        + model.cash[3],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.terminal_wealth))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
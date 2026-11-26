# IR: {"sets":{"years":[1,2,3]},"params":["initial_capital","rate_project1","multiplier_project2","cap_project2","multiplier_project3","cap_project3","multiplier_project4","cap_project4"],"variables":{"project1[years]":"continuous nonnegative","project2":"continuous nonnegative","project3":"continuous nonnegative","project4":"continuous nonnegative","cash[years]":"continuous nonnegative; uninvested cash carried forward without interest"},"constraints":["project1[1] + project2 + cash[1] = initial_capital","project1[2] + project3 + cash[2] = (1 + rate_project1)*project1[1] + cash[1]","project1[3] + project4 + cash[3] = (1 + rate_project1)*project1[2] + multiplier_project2*project2 + cash[2]","project2 <= cap_project2","project3 <= cap_project3","project4 <= cap_project4"],"objective":"maximize (1 + rate_project1)*project1[3] + multiplier_project3*project3 + multiplier_project4*project4 + cash[3]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_capital = params["initial_capital"]
    rate_project1 = params["rate_project1"]
    multiplier_project2 = params["multiplier_project2"]
    cap_project2 = params["cap_project2"]
    multiplier_project3 = params["multiplier_project3"]
    cap_project3 = params["cap_project3"]
    multiplier_project4 = params["multiplier_project4"]
    cap_project4 = params["cap_project4"]

    model = pyo.ConcreteModel()
    model.years = pyo.RangeSet(1, 3)

    model.project1 = pyo.Var(model.years, domain=pyo.NonNegativeReals)
    model.project2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.project3 = pyo.Var(domain=pyo.NonNegativeReals)
    model.project4 = pyo.Var(domain=pyo.NonNegativeReals)
    model.cash = pyo.Var(model.years, domain=pyo.NonNegativeReals)

    model.year1_balance = pyo.Constraint(
        expr=(
            model.project1[1] + model.project2 + model.cash[1]
            == initial_capital
        )
    )

    model.year2_balance = pyo.Constraint(
        expr=(
            model.project1[2] + model.project3 + model.cash[2]
            == (1 + rate_project1) * model.project1[1] + model.cash[1]
        )
    )

    model.year3_balance = pyo.Constraint(
        expr=(
            model.project1[3] + model.project4 + model.cash[3]
            == (
                (1 + rate_project1) * model.project1[2]
                + multiplier_project2 * model.project2
                + model.cash[2]
            )
        )
    )

    model.project2_limit = pyo.Constraint(
        expr=model.project2 <= cap_project2
    )
    model.project3_limit = pyo.Constraint(
        expr=model.project3 <= cap_project3
    )
    model.project4_limit = pyo.Constraint(
        expr=model.project4 <= cap_project4
    )

    model.final_wealth = pyo.Objective(
        expr=(
            (1 + rate_project1) * model.project1[3]
            + multiplier_project3 * model.project3
            + multiplier_project4 * model.project4
            + model.cash[3]
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.final_wealth))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
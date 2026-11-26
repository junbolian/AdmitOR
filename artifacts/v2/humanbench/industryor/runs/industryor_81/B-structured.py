# IR: {"sets":{"years":[1,2,3]},"params":["initial_capital","annual_reinvest_profit_rate","project2_total_interest_rate","project2_investment_cap","project3_total_interest_rate","project3_investment_cap","project4_profit_rate","project4_investment_cap"],"variables":{"annual[years]":"continuous nonnegative","idle[years]":"continuous nonnegative","project2":"continuous nonnegative","project3":"continuous nonnegative","project4":"continuous nonnegative"},"constraints":["annual[1]+project2+idle[1]=initial_capital","annual[2]+project3+idle[2]=(1+annual_reinvest_profit_rate)*annual[1]+idle[1]","annual[3]+project4+idle[3]=(1+annual_reinvest_profit_rate)*annual[2]+(1+project2_total_interest_rate)*project2+(1+project3_total_interest_rate)*project3+idle[2]","project2<=project2_investment_cap","project3<=project3_investment_cap","project4<=project4_investment_cap"],"objective":"maximize (1+annual_reinvest_profit_rate)*annual[3]+(1+project4_profit_rate)*project4+idle[3]-initial_capital"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.years = pyo.Set(initialize=[1, 2, 3], ordered=True)

    model.initial_capital = pyo.Param(
        initialize=params["initial_capital"]
    )
    model.annual_reinvest_profit_rate = pyo.Param(
        initialize=params["annual_reinvest_profit_rate"]
    )
    model.project2_total_interest_rate = pyo.Param(
        initialize=params["project2_total_interest_rate"]
    )
    model.project2_investment_cap = pyo.Param(
        initialize=params["project2_investment_cap"]
    )
    model.project3_total_interest_rate = pyo.Param(
        initialize=params["project3_total_interest_rate"]
    )
    model.project3_investment_cap = pyo.Param(
        initialize=params["project3_investment_cap"]
    )
    model.project4_profit_rate = pyo.Param(
        initialize=params["project4_profit_rate"]
    )
    model.project4_investment_cap = pyo.Param(
        initialize=params["project4_investment_cap"]
    )

    model.annual = pyo.Var(model.years, domain=pyo.NonNegativeReals)
    model.idle = pyo.Var(model.years, domain=pyo.NonNegativeReals)
    model.project2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.project3 = pyo.Var(domain=pyo.NonNegativeReals)
    model.project4 = pyo.Var(domain=pyo.NonNegativeReals)

    model.year1_balance = pyo.Constraint(
        expr=(
            model.annual[1] + model.project2 + model.idle[1]
            == model.initial_capital
        )
    )

    model.year2_balance = pyo.Constraint(
        expr=(
            model.annual[2] + model.project3 + model.idle[2]
            == (1 + model.annual_reinvest_profit_rate) * model.annual[1]
            + model.idle[1]
        )
    )

    model.year3_balance = pyo.Constraint(
        expr=(
            model.annual[3] + model.project4 + model.idle[3]
            == (1 + model.annual_reinvest_profit_rate) * model.annual[2]
            + (1 + model.project2_total_interest_rate) * model.project2
            + (1 + model.project3_total_interest_rate) * model.project3
            + model.idle[2]
        )
    )

    model.project2_limit = pyo.Constraint(
        expr=model.project2 <= model.project2_investment_cap
    )
    model.project3_limit = pyo.Constraint(
        expr=model.project3 <= model.project3_investment_cap
    )
    model.project4_limit = pyo.Constraint(
        expr=model.project4 <= model.project4_investment_cap
    )

    model.total_interest = pyo.Objective(
        expr=(
            (1 + model.annual_reinvest_profit_rate) * model.annual[3]
            + (1 + model.project4_profit_rate) * model.project4
            + model.idle[3]
            - model.initial_capital
        ),
        sense=pyo.maximize,
    )

    # APPsi HiGHS can raise RuntimeError when no solution can be loaded.
    # Objective retrievability remains the sole success criterion.
    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_interest))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solver_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}
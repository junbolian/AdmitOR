# IR: {"sets":{"I":[0,1,2,3,4],"C":["Argentina","Brazil","England","Spain","Germany"]},"params":{"security_price":"params['security_price'][i]","share_limit":"params['share_limit'][i]","payoff":"params['payoff'][i][c], country columns in C order"},"variables":{"shares[i]":"nonnegative continuous","worst_case_revenue":"real"},"constraints":["shares[i] <= share_limit[i] for every i","worst_case_revenue <= sum_i((payoff[i,c] - security_price[i])*shares[i]) for every c"],"objective":"maximize worst_case_revenue"}
# Revenue is net of purchase costs; fractional shares are permitted.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    security_price = params["security_price"]
    share_limit = params["share_limit"]
    payoff = params["payoff"]

    model = pyo.ConcreteModel()
    model.securities = pyo.RangeSet(0, 4)
    model.countries = pyo.Set(
        initialize=["Argentina", "Brazil", "England", "Spain", "Germany"],
        ordered=True,
    )
    country_column = {
        country: column
        for column, country in enumerate(model.countries)
    }

    model.purchase_price = pyo.Param(
        model.securities,
        initialize={
            security: security_price[security]
            for security in model.securities
        },
        within=pyo.Reals,
    )
    model.purchase_limit = pyo.Param(
        model.securities,
        initialize={
            security: share_limit[security]
            for security in model.securities
        },
        within=pyo.NonNegativeReals,
    )
    model.outcome_payoff = pyo.Param(
        model.securities,
        model.countries,
        initialize={
            (security, country): payoff[security][country_column[country]]
            for security in model.securities
            for country in model.countries
        },
        within=pyo.Reals,
    )

    model.shares = pyo.Var(
        model.securities,
        domain=pyo.NonNegativeReals,
    )
    model.worst_case_revenue = pyo.Var(domain=pyo.Reals)

    def purchase_limit_rule(problem, security):
        return problem.shares[security] <= problem.purchase_limit[security]

    model.share_cap = pyo.Constraint(
        model.securities,
        rule=purchase_limit_rule,
    )

    def outcome_revenue_rule(problem, country):
        return problem.worst_case_revenue <= sum(
            (
                problem.outcome_payoff[security, country]
                - problem.purchase_price[security]
            )
            * problem.shares[security]
            for security in problem.securities
        )

    model.revenue_guarantee = pyo.Constraint(
        model.countries,
        rule=outcome_revenue_rule,
    )
    model.max_revenue = pyo.Objective(
        expr=model.worst_case_revenue,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.max_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
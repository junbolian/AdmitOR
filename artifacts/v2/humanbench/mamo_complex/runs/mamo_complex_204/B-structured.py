# IR: {"sets":{"securities":[0,1,2,3,4],"countries":["Argentina","Brazil","England","Germany","Spain"]},"params":{"price":"params['price'][i]","share_limit":"params['share_limit'][i]","payoff":"params['payoff'][i][j], columns follow countries order"},"variables":{"shares[i]":"NonNegativeIntegers","worst_case_revenue":"Reals"},"constraints":["shares[i] <= share_limit[i] for each security i","worst_case_revenue <= sum(payoff[i,j]*shares[i] for i) - sum(price[i]*shares[i] for i) for each country j"],"objective":"maximize worst_case_revenue"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.securities = pyo.RangeSet(0, 4)
    model.countries = pyo.Set(
        initialize=["Argentina", "Brazil", "England", "Germany", "Spain"],
        ordered=True,
    )
    country_columns = {
        country: column
        for column, country in enumerate(model.countries)
    }

    model.purchase_price = pyo.Param(
        model.securities,
        initialize=lambda mdl, security: params["price"][security],
        within=pyo.Reals,
    )
    model.purchase_limit = pyo.Param(
        model.securities,
        initialize=lambda mdl, security: params["share_limit"][security],
        within=pyo.NonNegativeReals,
    )
    model.security_payoff = pyo.Param(
        model.securities,
        model.countries,
        initialize=lambda mdl, security, country: params["payoff"][security][
            country_columns[country]
        ],
        within=pyo.Reals,
    )

    model.shares = pyo.Var(
        model.securities,
        domain=pyo.NonNegativeIntegers,
    )
    model.worst_case_revenue = pyo.Var(domain=pyo.Reals)

    model.share_caps = pyo.Constraint(
        model.securities,
        rule=lambda mdl, security: (
            mdl.shares[security] <= mdl.purchase_limit[security]
        ),
    )

    def outcome_revenue_rule(mdl, country):
        return mdl.worst_case_revenue <= sum(
            (
                mdl.security_payoff[security, country]
                - mdl.purchase_price[security]
            )
            * mdl.shares[security]
            for security in mdl.securities
        )

    model.outcome_revenue_limits = pyo.Constraint(
        model.countries,
        rule=outcome_revenue_rule,
    )
    model.revenue_objective = pyo.Objective(
        expr=model.worst_case_revenue,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.revenue_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
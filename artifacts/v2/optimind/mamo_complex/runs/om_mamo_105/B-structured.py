# IR: {"sets":{"S":[0,1,2,3,4],"C":["Argentina","Brazil","England","Germany","Spain"]},"params":{"price":"price[s] from params['price'][s]","share_limit":"share_limit[s] from params['share_limit'][s]","payoff":"payoff[c,s] from params['payoff'][row(c)][s]"},"variables":{"shares[s]":"NonNegativeReals (fractional shares permitted)","worst_case_revenue":"Reals"},"constraints":["shares[s] <= share_limit[s] for every s in S","worst_case_revenue <= sum((payoff[c,s] - price[s])*shares[s] for s in S) for every c in C"],"objective":"maximize worst_case_revenue; revenue is payoff minus total purchasing cost"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price = params["price"]
    share_limit = params["share_limit"]
    payoff = params["payoff"]

    countries = ("Argentina", "Brazil", "England", "Germany", "Spain")

    model = pyo.ConcreteModel()
    model.security_ids = pyo.RangeSet(0, 4)
    model.country_ids = pyo.Set(initialize=countries, ordered=True)

    model.purchase_price = pyo.Param(
        model.security_ids,
        initialize={sec: price[sec] for sec in range(5)},
        within=pyo.Reals,
    )
    model.purchase_limit = pyo.Param(
        model.security_ids,
        initialize={sec: share_limit[sec] for sec in range(5)},
        within=pyo.Reals,
    )
    model.outcome_payoff = pyo.Param(
        model.country_ids,
        model.security_ids,
        initialize={
            (country, sec): payoff[row][sec]
            for row, country in enumerate(countries)
            for sec in range(5)
        },
        within=pyo.Reals,
    )

    model.shares = pyo.Var(model.security_ids, domain=pyo.NonNegativeReals)
    model.worst_case_revenue = pyo.Var(domain=pyo.Reals)

    def purchase_limit_rule(instance, sec):
        return instance.shares[sec] <= instance.purchase_limit[sec]

    model.purchase_limit_constraints = pyo.Constraint(
        model.security_ids, rule=purchase_limit_rule
    )

    def worst_case_rule(instance, country):
        return instance.worst_case_revenue <= sum(
            (
                instance.outcome_payoff[country, sec]
                - instance.purchase_price[sec]
            )
            * instance.shares[sec]
            for sec in instance.security_ids
        )

    model.outcome_constraints = pyo.Constraint(
        model.country_ids, rule=worst_case_rule
    )
    model.revenue_objective = pyo.Objective(
        expr=model.worst_case_revenue, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.revenue_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
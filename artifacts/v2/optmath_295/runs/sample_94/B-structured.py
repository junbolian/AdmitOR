# IR: {"sets":{"C":[0,1,2,3,4],"P":[0,1,2],"M":[0,1,2]},"params":{"demand":"real[P,M], from params['demand'][p][market]","profit":"real[C,P,M], from params['profit'][c][p][market]"},"variables":{"supply[c,p,market]":"continuous, nonnegative"},"constraints":["sum(c in C) supply[c,p,market] == demand[p,market] for each (p,market) in P x M"],"objective":"maximize sum((c,p,market) in C x P x M) profit[c,p,market] * supply[c,p,market]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    model = pyo.ConcreteModel()

    model.companies = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 2)
    model.markets = pyo.RangeSet(0, 2)

    model.demand = pyo.Param(
        model.products,
        model.markets,
        initialize=lambda mdl, product, market: demand[product][market],
        within=pyo.Reals,
    )
    model.profit = pyo.Param(
        model.companies,
        model.products,
        model.markets,
        initialize=lambda mdl, company, product, market: (
            profit[company][product][market]
        ),
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.products,
        model.markets,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(mdl, product, market):
        return (
            sum(
                mdl.supply[company, product, market]
                for company in mdl.companies
            )
            == mdl.demand[product, market]
        )

    model.demand_balance = pyo.Constraint(
        model.products,
        model.markets,
        rule=demand_balance_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[company, product, market]
            * model.supply[company, product, market]
            for company in model.companies
            for product in model.products
            for market in model.markets
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
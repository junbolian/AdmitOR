# IR: {"sets":{"C":[0,1,2,3],"P":[0,1],"K":[0,1,2,3]},"params":{"profit[c,p,k]":"params['profit'][c][p][k], real","demand[p,k]":"params['demand'][p][k], real"},"variables":{"supply[c,p,k]":"nonnegative continuous"},"constraints":["sum(supply[c,p,k] for c in C) == demand[p,k] for each p in P, k in K"],"objective":"maximize sum(profit[c,p,k]*supply[c,p,k] for c in C, p in P, k in K)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.companies = pyo.Set(initialize=range(4), ordered=True)
    model.products = pyo.Set(initialize=range(2), ordered=True)
    model.markets = pyo.Set(initialize=range(4), ordered=True)

    model.profit = pyo.Param(
        model.companies,
        model.products,
        model.markets,
        initialize={
            (company, product, market): params["profit"][company][product][market]
            for company in model.companies
            for product in model.products
            for market in model.markets
        },
        within=pyo.Reals,
    )

    model.demand = pyo.Param(
        model.products,
        model.markets,
        initialize={
            (product, market): params["demand"][product][market]
            for product in model.products
            for market in model.markets
        },
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.products,
        model.markets,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(instance, product, market):
        return (
            sum(
                instance.supply[company, product, market]
                for company in instance.companies
            )
            == instance.demand[product, market]
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
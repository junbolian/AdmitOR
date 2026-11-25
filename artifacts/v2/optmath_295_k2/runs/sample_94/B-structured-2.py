# IR: {"sets":{"companies":[0,1,2,3,4],"products":[0,1,2],"markets":[0,1,2]},"params":{"demand":"real[market][product] from params['demand']","profit":"real[company][product][market] from params['profit']"},"variables":{"supply":"nonnegative continuous[company,product,market]"},"constraints":["For each product and market: sum(supply[company,product,market] over companies) == demand[market,product]"],"objective":"maximize sum(profit[company,product,market] * supply[company,product,market] over companies, products, markets)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.companies = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 2)
    model.markets = pyo.RangeSet(0, 2)

    model.demand = pyo.Param(
        model.markets,
        model.products,
        initialize={
            (market, product): params["demand"][market][product]
            for market in model.markets
            for product in model.products
        },
        within=pyo.Reals,
    )

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

    model.supply = pyo.Var(
        model.companies,
        model.products,
        model.markets,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, product, market):
        return (
            sum(
                instance.supply[company, product, market]
                for company in instance.companies
            )
            == instance.demand[market, product]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.products,
        model.markets,
        rule=demand_rule,
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
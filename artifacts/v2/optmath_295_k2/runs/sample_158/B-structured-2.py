# IR: {"sets":{"C":[0,1,2],"K":[0,1,2,3],"P":[0,1]},"params":{"demand":{"source":"params['demand']","index":"2*k+p","type":"real"},"profit":{"source":"params['profit']","index":"8*c+2*k+p","type":"real"}},"variables":{"quantity[c,k,p]":"continuous, nonnegative"},"constraints":["sum(quantity[c,k,p] for c in C) == demand[2*k+p] for each (k,p) in K x P"],"objective":{"sense":"maximize","expression":"sum(profit[8*c+2*k+p]*quantity[c,k,p] for (c,k,p) in C x K x P)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = params["demand"]
    profit_data = params["profit"]

    model = pyo.ConcreteModel()

    model.companies = pyo.RangeSet(0, 2)
    model.markets = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 1)

    model.demand_requirement = pyo.Param(
        model.markets,
        model.products,
        initialize={
            (market, product): demand_data[2 * market + product]
            for market in model.markets
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.unit_profit = pyo.Param(
        model.companies,
        model.markets,
        model.products,
        initialize={
            (company, market, product): profit_data[
                8 * company + 2 * market + product
            ]
            for company in model.companies
            for market in model.markets
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.companies,
        model.markets,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(block, market, product):
        return (
            sum(
                block.quantity[company, market, product]
                for company in block.companies
            )
            == block.demand_requirement[market, product]
        )

    model.demand_balance = pyo.Constraint(
        model.markets,
        model.products,
        rule=demand_balance_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[company, market, product]
            * model.quantity[company, market, product]
            for company in model.companies
            for market in model.markets
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
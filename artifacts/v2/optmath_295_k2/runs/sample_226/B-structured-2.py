# IR: {"sets":{"companies":[0,1,2,3],"products":[0,1],"markets":[0,1,2,3]},"params":{"demand_p0_m0":"real","demand_p1_m0":"real","demand_p0_m1":"real","demand_p1_m1":"real","demand_p0_m2":"real","demand_p1_m2":"real","demand_p0_m3":"real","demand_p1_m3":"real","profit":"real[company][product][market]"},"variables":{"supply[company,product,market]":"continuous nonnegative"},"constraints":["For each product and market: sum(supply[company,product,market] for company in companies) = demand[product,market]."],"objective":"maximize sum(profit[company][product][market] * supply[company,product,market] for company in companies, product in products, market in markets)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = {
        (0, 0): params["demand_p0_m0"],
        (1, 0): params["demand_p1_m0"],
        (0, 1): params["demand_p0_m1"],
        (1, 1): params["demand_p1_m1"],
        (0, 2): params["demand_p0_m2"],
        (1, 2): params["demand_p1_m2"],
        (0, 3): params["demand_p0_m3"],
        (1, 3): params["demand_p1_m3"],
    }
    profit_data = params["profit"]

    model = pyo.ConcreteModel()
    model.companies = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 1)
    model.markets = pyo.RangeSet(0, 3)

    model.market_demand = pyo.Param(
        model.products,
        model.markets,
        initialize=demands,
        within=pyo.Reals,
    )
    model.unit_profit = pyo.Param(
        model.companies,
        model.products,
        model.markets,
        initialize={
            (company, product, market): profit_data[company][product][market]
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

    def demand_rule(mdl, product, market):
        return (
            sum(
                mdl.supply[company, product, market]
                for company in mdl.companies
            )
            == mdl.market_demand[product, market]
        )

    model.demand_balance = pyo.Constraint(
        model.products,
        model.markets,
        rule=demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[company, product, market]
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
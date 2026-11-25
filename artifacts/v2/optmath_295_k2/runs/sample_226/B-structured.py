# IR: {"sets":{"companies":[0,1,2,3],"products":[0,1],"markets":[0,1,2,3]},"params":{"demand[p,k]":"params['demand_p{p}_m{k}']","profit[c,p,k]":"params['profit'][c][p][k]"},"variables":{"supply[c,p,k]":{"type":"continuous","lower_bound":0}},"constraints":["For every product p and market k: sum(supply[c,p,k] for c in companies) == demand[p,k]"],"objective":{"sense":"maximize","expression":"sum(profit[c,p,k] * supply[c,p,k] for c in companies for p in products for k in markets)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = {
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

    model.demand = pyo.Param(
        model.products,
        model.markets,
        initialize=demand_data,
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

    def demand_rule(instance, product, market):
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
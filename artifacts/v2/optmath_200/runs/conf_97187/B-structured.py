# IR: {"sets":{"C":[0,1,2],"P":[0,1],"K":[0,1,2,3]},"params":{"demand_p0":"real[K]","demand_p1":"real[K]","profit_company0_product0":"real[K]","profit_company0_product1":"real[K]","profit_company1_product0":"real[K]","profit_company1_product1":"real[K]","profit_company2_product0":"real[K]","profit_company2_product1":"real[K]"},"variables":{"shipment[c,p,k]":"continuous >= 0"},"constraints":["For each p in P and k in K: sum(c in C, shipment[c,p,k]) = demand_p{p}[k]"],"objective":"maximize sum(c in C,p in P,k in K, profit_company{c}_product{p}[k] * shipment[c,p,k])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = {
        0: params["demand_p0"],
        1: params["demand_p1"],
    }
    profit_data = {
        (0, 0): params["profit_company0_product0"],
        (0, 1): params["profit_company0_product1"],
        (1, 0): params["profit_company1_product0"],
        (1, 1): params["profit_company1_product1"],
        (2, 0): params["profit_company2_product0"],
        (2, 1): params["profit_company2_product1"],
    }

    model = pyo.ConcreteModel()
    model.company_ids = pyo.RangeSet(0, 2)
    model.product_ids = pyo.RangeSet(0, 1)
    model.market_ids = pyo.RangeSet(0, 3)

    model.market_demand = pyo.Param(
        model.product_ids,
        model.market_ids,
        initialize={
            (product, market): demand_data[product][market]
            for product in model.product_ids
            for market in model.market_ids
        },
        within=pyo.Reals,
    )

    model.unit_profit = pyo.Param(
        model.company_ids,
        model.product_ids,
        model.market_ids,
        initialize={
            (company, product, market): profit_data[(company, product)][market]
            for company in model.company_ids
            for product in model.product_ids
            for market in model.market_ids
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.company_ids,
        model.product_ids,
        model.market_ids,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(instance, product, market):
        return (
            sum(
                instance.shipment[company, product, market]
                for company in instance.company_ids
            )
            == instance.market_demand[product, market]
        )

    model.demand_balance = pyo.Constraint(
        model.product_ids,
        model.market_ids,
        rule=demand_balance_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[company, product, market]
            * model.shipment[company, product, market]
            for company in model.company_ids
            for product in model.product_ids
            for market in model.market_ids
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
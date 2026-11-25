# IR: {"sets":{"companies":[0,1,2,3,4],"products":[0,1,2],"markets":[0,1,2]},"params":{"demand":"real[market][product], read from params","profit":"real[company][product][market], read from params"},"variables":{"supply[company,product,market]":"nonnegative continuous"},"constraints":["For each market and product: sum(supply[company,product,market] for company in companies) = demand[market][product]."],"objective":"Maximize sum(profit[company][product][market] * supply[company,product,market] for all companies, products, and markets)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = params["demand"]
    profit_data = params["profit"]

    model = pyo.ConcreteModel()

    model.companies = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 2)
    model.markets = pyo.RangeSet(0, 2)

    model.demand = pyo.Param(
        model.markets,
        model.products,
        initialize=lambda block, market, product: demand_data[market][product],
        within=pyo.Reals,
    )

    model.profit = pyo.Param(
        model.companies,
        model.products,
        model.markets,
        initialize=lambda block, company, product, market: (
            profit_data[company][product][market]
        ),
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.products,
        model.markets,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(block, market, product):
        return (
            sum(
                block.supply[company, product, market]
                for company in block.companies
            )
            == block.demand[market, product]
        )

    model.demand_balance = pyo.Constraint(
        model.markets,
        model.products,
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
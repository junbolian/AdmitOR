# IR: {"sets":{"suppliers":[0,1,2],"products":[0,1,2],"markets":[0,1]},"params":{"demand_market0":"vector[products]","demand_market1":"vector[products]","profit_supplier0_market0":"vector[products]","profit_supplier0_market1":"vector[products]","profit_supplier1_market0":"vector[products]","profit_supplier1_market1":"vector[products]","profit_supplier2_market0":"vector[products]","profit_supplier2_market1":"vector[products]"},"variables":{"quantity[s,p,k]":"nonnegative continuous"},"constraints":["For each product p and market k: sum(quantity[s,p,k] for s in suppliers) = demand_market{k}[p]"],"objective":"maximize sum(profit_supplier{s}_market{k}[p] * quantity[s,p,k] for s in suppliers, p in products, k in markets)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_vectors = {
        0: params["demand_market0"],
        1: params["demand_market1"],
    }
    profit_vectors = {
        (0, 0): params["profit_supplier0_market0"],
        (0, 1): params["profit_supplier0_market1"],
        (1, 0): params["profit_supplier1_market0"],
        (1, 1): params["profit_supplier1_market1"],
        (2, 0): params["profit_supplier2_market0"],
        (2, 1): params["profit_supplier2_market1"],
    }

    model = pyo.ConcreteModel()
    model.suppliers = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.products = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.markets = pyo.Set(initialize=[0, 1], ordered=True)

    model.demand = pyo.Param(
        model.products,
        model.markets,
        initialize={
            (product, market): demand_vectors[market][product]
            for product in model.products
            for market in model.markets
        },
        within=pyo.Reals,
    )
    model.profit = pyo.Param(
        model.suppliers,
        model.products,
        model.markets,
        initialize={
            (supplier, product, market): profit_vectors[supplier, market][product]
            for supplier in model.suppliers
            for product in model.products
            for market in model.markets
        },
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.suppliers,
        model.products,
        model.markets,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, product, market):
        return (
            sum(
                instance.quantity[supplier, product, market]
                for supplier in instance.suppliers
            )
            == instance.demand[product, market]
        )

    model.exact_demand = pyo.Constraint(
        model.products, model.markets, rule=demand_rule
    )
    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[supplier, product, market]
            * model.quantity[supplier, product, market]
            for supplier in model.suppliers
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
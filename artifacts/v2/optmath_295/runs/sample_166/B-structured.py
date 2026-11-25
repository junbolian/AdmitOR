# IR: {"sets":{"S":[0,1,2,3],"P":[0,1],"R":[0,1,2,3,4]},"params":{"demand":{"shape":[10],"index":"5*p+r"},"profit_margin":{"shape":[4,2,5],"index":"[s][p][r]"}},"variables":{"supply[s,p,r]":"NonNegativeReals"},"constraints":["sum(supply[s,p,r] for s in S) == demand[5*p+r] for each p in P, r in R"],"objective":"maximize sum(profit_margin[s][p][r] * supply[s,p,r] for s in S, p in P, r in R)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit_margin = params["profit_margin"]

    model = pyo.ConcreteModel()

    model.suppliers = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 1)
    model.regions = pyo.RangeSet(0, 4)

    model.required_demand = pyo.Param(
        model.products,
        model.regions,
        initialize={
            (product, region): demand[5 * product + region]
            for product in model.products
            for region in model.regions
        },
        within=pyo.Reals,
    )

    model.unit_profit = pyo.Param(
        model.suppliers,
        model.products,
        model.regions,
        initialize={
            (supplier, product, region): profit_margin[supplier][product][region]
            for supplier in model.suppliers
            for product in model.products
            for region in model.regions
        },
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.suppliers,
        model.products,
        model.regions,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(mdl, product, region):
        return (
            sum(
                mdl.supply[supplier, product, region]
                for supplier in mdl.suppliers
            )
            == mdl.required_demand[product, region]
        )

    model.demand_balance = pyo.Constraint(
        model.products,
        model.regions,
        rule=demand_balance_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[supplier, product, region]
            * model.supply[supplier, product, region]
            for supplier in model.suppliers
            for product in model.products
            for region in model.regions
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
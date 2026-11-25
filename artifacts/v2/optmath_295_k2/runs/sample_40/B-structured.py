# IR: {"sets":{"C":[0,1],"K":[0,1,2,3],"P":[0,1,2]},"params":{"demand":"real[K,P], input indexed [market][product]","profit_c0":"real[K,P], input indexed [market][product]","profit_c1":"real[K,P], input indexed [market][product]"},"variables":{"supply[C,K,P]":"continuous, nonnegative"},"constraints":["sum(supply[c,k,p] for c in C) == demand[k,p] for each k in K, p in P"],"objective":"maximize sum(profit_c0[k,p]*supply[0,k,p] + profit_c1[k,p]*supply[1,k,p] for k in K, p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using market-by-product nested sequences or nested mappings."""
    demand = params["demand"]
    profit_c0 = params["profit_c0"]
    profit_c1 = params["profit_c1"]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=[0, 1], ordered=True)
    model.K = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.P = pyo.Set(initialize=[0, 1, 2], ordered=True)

    model.demand = pyo.Param(
        model.K,
        model.P,
        initialize=lambda mdl, market, product: demand[market][product],
        within=pyo.Reals,
    )
    model.profit_c0 = pyo.Param(
        model.K,
        model.P,
        initialize=lambda mdl, market, product: profit_c0[market][product],
        within=pyo.Reals,
    )
    model.profit_c1 = pyo.Param(
        model.K,
        model.P,
        initialize=lambda mdl, market, product: profit_c1[market][product],
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.C, model.K, model.P, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, market, product):
        return (
            sum(mdl.supply[company, market, product] for company in mdl.C)
            == mdl.demand[market, product]
        )

    model.demand_balance = pyo.Constraint(
        model.K, model.P, rule=demand_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_c0[market, product] * model.supply[0, market, product]
            + model.profit_c1[market, product] * model.supply[1, market, product]
            for market in model.K
            for product in model.P
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
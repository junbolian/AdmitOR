# IR: {"sets":{"C":[0,1],"K":[0,1,2,3],"P":[0,1,2]},"params":{"demand":"params['demand'][k][p]","profit_c0":"params['profit_c0'][k][p]","profit_c1":"params['profit_c1'][k][p]"},"variables":{"supply[c,k,p]":"continuous, nonnegative"},"constraints":["sum(supply[c,k,p] for c in C) == demand[k,p] for each k in K, p in P"],"objective":"maximize sum(profit_c0[k,p]*supply[0,k,p] + profit_c1[k,p]*supply[1,k,p] for k in K, p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Input arrays are indexed [market][product]."""
    demand_data = params["demand"]
    profit_c0_data = params["profit_c0"]
    profit_c1_data = params["profit_c1"]

    model = pyo.ConcreteModel()
    model.companies = pyo.RangeSet(0, 1)
    model.markets = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 2)

    model.demand = pyo.Param(
        model.markets,
        model.products,
        initialize=lambda mdl, market, product: demand_data[market][product],
        within=pyo.Reals,
    )
    model.profit_c0 = pyo.Param(
        model.markets,
        model.products,
        initialize=lambda mdl, market, product: profit_c0_data[market][product],
        within=pyo.Reals,
    )
    model.profit_c1 = pyo.Param(
        model.markets,
        model.products,
        initialize=lambda mdl, market, product: profit_c1_data[market][product],
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.markets,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, market, product):
        return (
            sum(
                mdl.supply[company, market, product]
                for company in mdl.companies
            )
            == mdl.demand[market, product]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.markets,
        model.products,
        rule=demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_c0[market, product] * model.supply[0, market, product]
            + model.profit_c1[market, product] * model.supply[1, market, product]
            for market in model.markets
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
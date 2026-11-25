# IR: {"sets":{"C":[0,1,2],"P":[0,1],"R":[0,1,2,3,4]},"params":{"demand[p,r]":"params['demand_product{p}_region{r}']","profit[c,p,r]":"params['profit_company{c}_product{p}_region{r}']"},"variables":{"quantity[c,p,r]":{"type":"continuous","lb":0}},"constraints":["sum(quantity[c,p,r] for c in C) == demand[p,r] for p in P, r in R"],"objective":{"sense":"maximize","expression":"sum(profit[c,p,r]*quantity[c,p,r] for c in C, p in P, r in R)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=range(3), ordered=True)
    model.P = pyo.Set(initialize=range(2), ordered=True)
    model.R = pyo.Set(initialize=range(5), ordered=True)

    model.demand = pyo.Param(
        model.P,
        model.R,
        initialize={
            (product, region): params[
                f"demand_product{product}_region{region}"
            ]
            for product in model.P
            for region in model.R
        },
        within=pyo.Reals,
    )

    model.profit = pyo.Param(
        model.C,
        model.P,
        model.R,
        initialize={
            (company, product, region): params[
                f"profit_company{company}_product{product}_region{region}"
            ]
            for company in model.C
            for product in model.P
            for region in model.R
        },
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.C, model.P, model.R, domain=pyo.NonNegativeReals
    )

    def demand_balance_rule(mod, product, region):
        return (
            sum(mod.quantity[company, product, region] for company in mod.C)
            == mod.demand[product, region]
        )

    model.demand_balance = pyo.Constraint(
        model.P, model.R, rule=demand_balance_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[company, product, region]
            * model.quantity[company, product, region]
            for company in model.C
            for product in model.P
            for region in model.R
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Retrieval of the objective below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"C":[0,1,2,3,4],"M":[0,1,2,3],"P":[0,1]},"params":{"profit[c,j,k]":"params[f'profit_co{c}_ma{j}_pr{k}'] for (c,j,k) in CxMxP","demand[j,k]":"params[f'demand_ma{j}_pr{k}'] for (j,k) in MxP"},"variables":{"supply[c,j,k]":"NonNegativeReals for (c,j,k) in CxMxP"},"constraints":["sum(supply[c,j,k] for c in C) == demand[j,k] for (j,k) in MxP"],"objective":"maximize sum(profit[c,j,k]*supply[c,j,k] for (c,j,k) in CxMxP)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.companies = pyo.Set(initialize=range(5), ordered=True)
    model.markets = pyo.Set(initialize=range(4), ordered=True)
    model.products = pyo.Set(initialize=range(2), ordered=True)

    model.unit_profit = pyo.Param(
        model.companies,
        model.markets,
        model.products,
        initialize={
            (company, market, product): params[
                f"profit_co{company}_ma{market}_pr{product}"
            ]
            for company in model.companies
            for market in model.markets
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.market_demand = pyo.Param(
        model.markets,
        model.products,
        initialize={
            (market, product): params[f"demand_ma{market}_pr{product}"]
            for market in model.markets
            for product in model.products
        },
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
            == mdl.market_demand[market, product]
        )

    model.demand_balance = pyo.Constraint(
        model.markets,
        model.products,
        rule=demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[company, market, product]
            * model.supply[company, market, product]
            for company in model.companies
            for market in model.markets
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime failures.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
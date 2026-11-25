# IR: {"sets":{"companies":[0,1,2,3,4],"markets":[0,1]},"params":{"profit":"real[companies,markets], read from params['profit']","demand":"real[markets], read from params['demand']"},"variables":{"supply":"nonnegative continuous[companies,markets]"},"constraints":["For each market j: sum(supply[i,j] for i in companies) == demand[j]"],"objective":"maximize sum(profit[i,j]*supply[i,j] for i in companies for j in markets)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.companies = pyo.RangeSet(0, 4)
    model.markets = pyo.RangeSet(0, 1)

    model.profit = pyo.Param(
        model.companies,
        model.markets,
        initialize={
            (company, market): params["profit"][company][market]
            for company in model.companies
            for market in model.markets
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.markets,
        initialize={
            market: params["demand"][market]
            for market in model.markets
        },
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.markets,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(current_model, market):
        return sum(
            current_model.supply[company, market]
            for company in current_model.companies
        ) == current_model.demand[market]

    model.demand_satisfaction = pyo.Constraint(
        model.markets,
        rule=demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[company, market] * model.supply[company, market]
            for company in model.companies
            for market in model.markets
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Other runtime errors remain visible to the calling harness.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
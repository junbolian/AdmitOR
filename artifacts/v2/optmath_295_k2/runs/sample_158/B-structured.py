# IR: {"sets":{"C":[0,1,2],"M":[0,1,2,3],"P":[0,1]},"params":{"demand":{"shape":[8],"index":"2*j+k"},"profit":{"shape":[24],"index":"8*i+2*j+k"}},"variables":{"x[i,j,k]":{"indices":"C x M x P","type":"continuous","lower_bound":0}},"constraints":["sum(x[i,j,k] for i in C) == demand[2*j+k] for j in M, k in P"],"objective":{"sense":"maximize","expression":"sum(profit[8*i+2*j+k]*x[i,j,k] for i in C, j in M, k in P)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using flat demand and profit sequences in the specified order."""
    demand = params["demand"]
    profit = params["profit"]

    model = pyo.ConcreteModel()

    model.companies = pyo.RangeSet(0, 2)
    model.markets = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 1)

    model.required_demand = pyo.Param(
        model.markets,
        model.products,
        initialize=lambda mdl, j, k: demand[2 * j + k],
        within=pyo.Reals,
    )
    model.unit_profit = pyo.Param(
        model.companies,
        model.markets,
        model.products,
        initialize=lambda mdl, i, j, k: profit[8 * i + 2 * j + k],
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.markets,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, j, k):
        return (
            sum(mdl.supply[i, j, k] for i in mdl.companies)
            == mdl.required_demand[j, k]
        )

    model.demand_balance = pyo.Constraint(
        model.markets,
        model.products,
        rule=demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[i, j, k] * model.supply[i, j, k]
            for i in model.companies
            for j in model.markets
            for k in model.products
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
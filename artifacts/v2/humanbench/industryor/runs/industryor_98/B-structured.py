# IR: {"sets":{"T":[0,1,2],"B":[0,1]},"params":["initial_capital","profit_rate_1yr","profit_rate_2yr"],"variables":{"annual[T]":"continuous >= 0","biennial[B]":"continuous >= 0","cash[T]":"continuous >= 0"},"constraints":["annual[0] + biennial[0] + cash[0] = initial_capital","annual[1] + biennial[1] + cash[1] = cash[0] + (1 + profit_rate_1yr)*annual[0]","annual[2] + cash[2] = cash[1] + (1 + profit_rate_1yr)*annual[1] + (1 + profit_rate_2yr)*biennial[0]"],"objective":"maximize cash[2] + (1 + profit_rate_1yr)*annual[2] + (1 + profit_rate_2yr)*biennial[1]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_capital = params["initial_capital"]
    profit_rate_1yr = params["profit_rate_1yr"]
    profit_rate_2yr = params["profit_rate_2yr"]

    model = pyo.ConcreteModel()

    # Times are measured from the beginning of the investment horizon.
    # Each biennial investment remains invested for exactly two years.
    model.T = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.B = pyo.Set(initialize=[0, 1], ordered=True)

    model.initial_capital = pyo.Param(initialize=initial_capital)
    model.profit_rate_1yr = pyo.Param(initialize=profit_rate_1yr)
    model.profit_rate_2yr = pyo.Param(initialize=profit_rate_2yr)

    model.annual = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.biennial = pyo.Var(model.B, domain=pyo.NonNegativeReals)
    model.cash = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    model.initial_budget = pyo.Constraint(
        expr=model.annual[0] + model.biennial[0] + model.cash[0]
        == model.initial_capital
    )

    model.year_one_budget = pyo.Constraint(
        expr=model.annual[1] + model.biennial[1] + model.cash[1]
        == model.cash[0]
        + (1 + model.profit_rate_1yr) * model.annual[0]
    )

    model.year_two_budget = pyo.Constraint(
        expr=model.annual[2] + model.cash[2]
        == model.cash[1]
        + (1 + model.profit_rate_1yr) * model.annual[1]
        + (1 + model.profit_rate_2yr) * model.biennial[0]
    )

    # Terminal wealth includes returned principal and investment profits.
    model.terminal_wealth = pyo.Objective(
        expr=model.cash[2]
        + (1 + model.profit_rate_1yr) * model.annual[2]
        + (1 + model.profit_rate_2yr) * model.biennial[1],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when no feasible solution can be loaded.
        # Propagate unrelated runtime errors.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.terminal_wealth))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
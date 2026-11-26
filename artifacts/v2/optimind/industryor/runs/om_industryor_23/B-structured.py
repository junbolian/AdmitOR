# IR: {"sets":{"T1":[0,1,2],"T2":[0,1]},"params":{"total_capital":"initial capital","return_rate_option1":"total payout per yuan after one year","return_rate_option2":"total payout per yuan after two years"},"variables":{"x1[t in T1]":"NonNegativeReals; one-year investment starting at time t","x2[t in T2]":"NonNegativeReals; two-year investment starting at time t"},"constraints":["x1[0]+x2[0]=total_capital","x1[1]+x2[1]=return_rate_option1*x1[0]","x1[2]=return_rate_option1*x1[1]+return_rate_option2*x2[0]"],"objective":"maximize return_rate_option1*x1[2]+return_rate_option2*x2[1]"}
#
# Time 0 is the beginning of the first year; time 3 is the horizon.
# All initial capital and intermediate payouts are reinvested.
# Only investments maturing by time 3 are permitted.
# Return rates are total payout multipliers, including any returned principal.
# Maximizing terminal wealth also maximizes profit because initial capital is fixed.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.T1 = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.T2 = pyo.Set(initialize=[0, 1], ordered=True)

    model.total_capital = pyo.Param(
        initialize=params["total_capital"],
        within=pyo.NonNegativeReals,
    )
    model.return_rate_option1 = pyo.Param(
        initialize=params["return_rate_option1"],
        within=pyo.NonNegativeReals,
    )
    model.return_rate_option2 = pyo.Param(
        initialize=params["return_rate_option2"],
        within=pyo.NonNegativeReals,
    )

    model.x1 = pyo.Var(model.T1, domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(model.T2, domain=pyo.NonNegativeReals)

    model.initial_balance = pyo.Constraint(
        expr=model.x1[0] + model.x2[0] == model.total_capital
    )
    model.year_one_balance = pyo.Constraint(
        expr=model.x1[1] + model.x2[1]
        == model.return_rate_option1 * model.x1[0]
    )
    model.year_two_balance = pyo.Constraint(
        expr=model.x1[2]
        == model.return_rate_option1 * model.x1[1]
        + model.return_rate_option2 * model.x2[0]
    )

    model.terminal_wealth = pyo.Objective(
        expr=model.return_rate_option1 * model.x1[2]
        + model.return_rate_option2 * model.x2[1],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.terminal_wealth))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
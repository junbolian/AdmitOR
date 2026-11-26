import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    prod_time = params["prod_time_hours"]
    rate = params["rate_m_per_hour"]
    curtain_demand = params["curtain_demand_m"]
    clothing_demand = params["clothing_demand_m"]
    curtain_profit = params["curtain_profit_per_m"]
    clothing_profit = params["clothing_profit_per_m"]
    overtime_cap = params["overtime_cap_hours"]

    model = pyo.ConcreteModel()

    # Decision variables (meters produced per week)
    model.xC = pyo.Var(domain=pyo.NonNegativeReals)  # curtain fabric
    model.xL = pyo.Var(domain=pyo.NonNegativeReals)  # clothing fabric

    # Hours used and overtime
    model.hours_used = pyo.Expression(expr=(model.xC + model.xL) / rate)
    model.d_plus = pyo.Var(domain=pyo.NonNegativeReals)   # overtime hours (over target)
    model.d_minus = pyo.Var(domain=pyo.NonNegativeReals)  # idle hours (under target)

    # p1: use full available time -> hours_used + d_minus - d_plus == prod_time
    model.c_p1 = pyo.Constraint(
        expr=model.hours_used + model.d_minus - model.d_plus == prod_time
    )

    # Deviations for p2 (overtime cap), p3 (curtain/clothing demand), p4
    model.o_plus = pyo.Var(domain=pyo.NonNegativeReals)    # overtime beyond cap
    model.o_minus = pyo.Var(domain=pyo.NonNegativeReals)   # slack below cap
    model.c_p2 = pyo.Constraint(expr=model.d_plus - overtime_cap + model.o_minus - model.o_plus == 0)

    # p3: sell no less than demands, weighted by profit
    model.sC_plus = pyo.Var(domain=pyo.NonNegativeReals)
    model.sC_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.sL_plus = pyo.Var(domain=pyo.NonNegativeReals)
    model.sL_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_p3C = pyo.Constraint(
        expr=model.xC - curtain_demand + model.sC_minus - model.sC_plus == 0
    )
    model.c_p3L = pyo.Constraint(
        expr=model.xL - clothing_demand + model.sL_minus - model.sL_plus == 0
    )

    # p4: minimize overtime -> represented by d_plus, already included

    # Weighted single objective: prioritize p1, then p2, then weighted p3, then p4
    # Use large weights for higher priorities.
    W1 = 1e9
    W2 = 1e7
    W4 = 1e3
    model.obj = pyo.Objective(
        expr=(
            W1 * (model.d_plus + model.d_minus)
            + W2 * (model.o_plus)
            + (curtain_profit * (model.sC_minus + model.sC_plus)
               + clothing_profit * (model.sL_minus + model.sL_plus))
            + W4 * model.d_plus
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
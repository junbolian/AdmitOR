import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)

    pA = params["profit_A"]
    pB = params["profit_B"]
    t1A = params["time_procI_A"]
    t1B = params["time_procI_B"]
    t2A = params["time_procII_A"]
    t2B = params["time_procII_B"]
    cap1 = params["cap_procI"]
    cap2 = params["cap_procII"]
    profit_target = params["profit_target"]
    minA = params["min_A"]
    minB = params["min_B"]
    procI_target = params["procI_target"]

    # Deviation variables
    # p1: profit >= target -> minimize d1_minus
    model.d1_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d1_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # p2: contractual minimums -> minimize d2A_minus, d2B_minus
    model.d2A_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2A_plus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2B_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2B_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # p3 process I exact target -> minimize d3I_minus + d3I_plus
    model.d3I_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d3I_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # p3 process II maximized (even with overtime) -> minimize d3II_minus
    model.d3II_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d3II_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # p1 goal: profit constraint
    model.profit_goal = pyo.Constraint(
        expr=pA * model.xA + pB * model.xB + model.d1_minus - model.d1_plus
        == profit_target
    )

    # p2 goal: contractual minimums
    model.goal_min_A = pyo.Constraint(
        expr=model.xA + model.d2A_minus - model.d2A_plus == minA
    )
    model.goal_min_B = pyo.Constraint(
        expr=model.xB + model.d2B_minus - model.d2B_plus == minB
    )

    # p3 goal: Process I exact time
    model.goal_procI = pyo.Constraint(
        expr=t1A * model.xA + t1B * model.xB + model.d3I_minus - model.d3I_plus
        == procI_target
    )

    # p3 goal: Process II time (to be maximized, allow overtime)
    model.goal_procII = pyo.Constraint(
        expr=t2A * model.xA + t2B * model.xB + model.d3II_minus - model.d3II_plus
        == cap2
    )

    # Preemptive (lexicographic) weights: p1 >> p2 >> p3
    W1 = 1e8
    W2 = 1e4
    W3 = 1.0

    # Objective: weighted deviations
    model.obj = pyo.Objective(
        expr=(
            W1 * model.d1_minus
            + W2 * (model.d2A_minus + model.d2B_minus)
            + W3 * (model.d3I_minus + model.d3I_plus + model.d3II_minus)
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    profit_target = params["profit_target"]
    time_I_A = params["time_I_A"]
    time_I_B = params["time_I_B"]
    time_II_A = params["time_II_A"]
    time_II_B = params["time_II_B"]
    cap_I = params["cap_I"]
    cap_II = params["cap_II"]
    overtime_cap_II = params["overtime_cap_II"]
    min_A = params["min_A"]
    min_B = params["min_B"]
    overtime_penalty_A = params["overtime_penalty_A"]
    overtime_penalty_B = params["overtime_penalty_B"]

    model = pyo.ConcreteModel()

    # Decision variables
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)
    model.overII = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, overtime_cap_II))

    # Process II overtime is allocated to models (units processed in overtime)
    model.yA = pyo.Var(domain=pyo.NonNegativeReals)
    model.yB = pyo.Var(domain=pyo.NonNegativeReals)

    # Deviational variables (level 1)
    model.d1_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d1_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # Deviational variables (level 2)
    model.d2A_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2A_plus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2B_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2B_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # Deviational variables (level 3 - process I under/over, process II idleness)
    model.d3I_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d3I_plus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d3II_idle = pyo.Var(domain=pyo.NonNegativeReals)

    # Constraints
    # Process I capacity (regular)
    model.capI = pyo.Constraint(
        expr=time_I_A * model.xA + time_I_B * model.xB <= cap_I
    )

    # Process II regular capacity
    model.capII = pyo.Constraint(
        expr=time_II_A * model.xA + time_II_B * model.xB
        <= cap_II + model.overII
    )

    # Overtime allocation consistency: total overtime = units processed in overtime times time
    model.overAlloc = pyo.Constraint(
        expr=time_II_A * model.yA + time_II_B * model.yB == model.overII
    )

    # Overtime units cannot exceed total units produced
    model.yA_le = pyo.Constraint(expr=model.yA <= model.xA)
    model.yB_le = pyo.Constraint(expr=model.yB <= model.xB)

    # Level 1: profit target
    profit_expr = (
        profit_A * model.xA + profit_B * model.xB
        - overtime_penalty_A * model.yA - overtime_penalty_B * model.yB
    )
    model.p1 = pyo.Constraint(
        expr=profit_expr + model.d1_minus - model.d1_plus == profit_target
    )

    # Level 2: contractual minimums
    model.p2A = pyo.Constraint(
        expr=model.xA + model.d2A_minus - model.d2A_plus == min_A
    )
    model.p2B = pyo.Constraint(
        expr=model.xB + model.d2B_minus - model.d2B_plus == min_B
    )

    # Level 3: process I exactly at capacity; process II used to the max (including overtime)
    model.p3I = pyo.Constraint(
        expr=time_I_A * model.xA + time_I_B * model.xB
        + model.d3I_minus - model.d3I_plus == cap_I
    )
    model.p3II = pyo.Constraint(
        expr=time_II_A * model.xA + time_II_B * model.xB
        + model.d3II_idle == cap_II + overtime_cap_II
    )

    # Objective: lexicographic minimization
    # Weights must dominate prior-priority deviations.
    w1 = 1e10
    w2 = 1e7
    w3 = 1e4
    w4 = 1.0

    model.obj = pyo.Objective(
        expr=(
            w1 * model.d1_minus
            + w2 * (model.d2A_minus + model.d2B_minus)
            + w3 * (model.d3I_minus + model.d3I_plus + model.d3II_idle)
            + w4 * (overtime_penalty_A * model.yA + overtime_penalty_B * model.yB)
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
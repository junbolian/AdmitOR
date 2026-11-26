import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: units of A and B produced
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)

    # Overtime hours for process II
    model.oT = pyo.Var(domain=pyo.NonNegativeReals)

    # Contract minimums
    model.minA = pyo.Constraint(expr=model.xA >= params["min_units_A"])
    model.minB = pyo.Constraint(expr=model.xB >= params["min_units_B"])

    # Process I capacity
    model.capI = pyo.Constraint(
        expr=params["process_I_hours_A"] * model.xA
        + params["process_I_hours_B"] * model.xB
        <= params["capacity_I"]
    )

    # Process II regular capacity + overtime
    model.capII = pyo.Constraint(
        expr=params["process_II_hours_A"] * model.xA
        + params["process_II_hours_B"] * model.xB
        <= params["capacity_II"] + model.oT
    )

    # Overtime limit
    model.maxOT = pyo.Constraint(expr=model.oT <= params["max_overtime_II"])

    # Profit target
    base_profit = params["profit_A"] * model.xA + params["profit_B"] * model.xB
    overtime_penalty = (
        params["overtime_reduction_A"] * model.xA
        + params["overtime_reduction_B"] * model.xB
    )
    model.profitTarget = pyo.Constraint(
        expr=base_profit - overtime_penalty >= params["profit_target"]
    )

    # Objective: prefer fully utilizing process II (minimize slack/overtime used)
    # Maximize total profit as primary objective
    model.obj = pyo.Objective(
        expr=base_profit - overtime_penalty, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}
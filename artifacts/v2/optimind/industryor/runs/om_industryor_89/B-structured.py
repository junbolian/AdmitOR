# IR: {"sets":{"products":["A","B"]},"params":["profit_A","profit_B","assembly_time_A","assembly_time_B","weekly_machine_hours","ratio_A_per_5","ratio_B_min"],"variables":{"quantity_A":{"type":"NonNegativeReals"},"quantity_B":{"type":"NonNegativeReals"}},"constraints":["assembly_time_A*quantity_A + assembly_time_B*quantity_B <= 60*weekly_machine_hours","ratio_A_per_5*quantity_B >= ratio_B_min*quantity_A"],"objective":{"sense":"maximize","expression":"profit_A*quantity_A + profit_B*quantity_B"},"constants":{"minutes_per_hour":60}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.profit_A = pyo.Param(initialize=params["profit_A"])
    model.profit_B = pyo.Param(initialize=params["profit_B"])
    model.assembly_time_A = pyo.Param(initialize=params["assembly_time_A"])
    model.assembly_time_B = pyo.Param(initialize=params["assembly_time_B"])
    model.weekly_machine_hours = pyo.Param(
        initialize=params["weekly_machine_hours"]
    )
    model.ratio_A_per_5 = pyo.Param(initialize=params["ratio_A_per_5"])
    model.ratio_B_min = pyo.Param(initialize=params["ratio_B_min"])

    # Continuous production quantities, as in a linear programming formulation.
    model.quantity_A = pyo.Var(domain=pyo.NonNegativeReals)
    model.quantity_B = pyo.Var(domain=pyo.NonNegativeReals)

    model.machine_capacity = pyo.Constraint(
        expr=(
            model.assembly_time_A * model.quantity_A
            + model.assembly_time_B * model.quantity_B
            <= 60 * model.weekly_machine_hours
        )
    )

    model.technical_ratio = pyo.Constraint(
        expr=(
            model.ratio_A_per_5 * model.quantity_B
            >= model.ratio_B_min * model.quantity_A
        )
    )

    model.total_profit = pyo.Objective(
        expr=(
            model.profit_A * model.quantity_A
            + model.profit_B * model.quantity_B
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
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
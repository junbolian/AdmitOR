# IR: {"sets":{"products":["mw","wh"],"workshops":["A","B"],"priorities":[1,2,3,4,5]},"params":["labor_A","assembly_B","labor_A_heater","assembly_B_heater","inspect_cost_mw","inspect_cost_wh","cap_A","cap_B","cost_A","cost_B","demand_mw","demand_wh","inspect_budget","target_mw","target_wh","overtime_A_cap"],"variables":{"production[products]":"nonnegative real","idle[workshops]":"nonnegative real","overtime[workshops]":"nonnegative real","inspection_excess":"nonnegative real","mw_shortfall":"nonnegative real","A_overtime_excess":"nonnegative real","wh_shortfall":"nonnegative real"},"constraints":["production[mw] <= demand_mw","production[wh] <= demand_wh","labor_A*production[mw] + labor_A_heater*production[wh] + idle[A] - overtime[A] = cap_A","assembly_B*production[mw] + assembly_B_heater*production[wh] + idle[B] - overtime[B] = cap_B","inspect_cost_mw*production[mw] + inspect_cost_wh*production[wh] <= inspect_budget + inspection_excess","production[mw] + mw_shortfall >= target_mw","overtime[A] <= overtime_A_cap + A_overtime_excess","production[wh] + wh_shortfall >= target_wh","After each priority except the last, fix its objective expression equal to its retrieved optimum"],"objective":{"sense":"lexicographic minimize","expressions":["inspection_excess","mw_shortfall","cost_A*idle[A] + cost_B*idle[B]","A_overtime_excess","wh_shortfall"],"returned_value":"final priority objective"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    labor_A = params["labor_A"]
    assembly_B = params["assembly_B"]
    labor_A_heater = params["labor_A_heater"]
    assembly_B_heater = params["assembly_B_heater"]
    inspect_cost_mw = params["inspect_cost_mw"]
    inspect_cost_wh = params["inspect_cost_wh"]
    cap_A = params["cap_A"]
    cap_B = params["cap_B"]
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    demand_mw = params["demand_mw"]
    demand_wh = params["demand_wh"]
    inspect_budget = params["inspect_budget"]
    target_mw = params["target_mw"]
    target_wh = params["target_wh"]
    overtime_A_cap = params["overtime_A_cap"]

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["mw", "wh"], ordered=True)
    model.workshops = pyo.Set(initialize=["A", "B"], ordered=True)

    # Production quantities are continuous because integrality is not specified.
    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.idle = pyo.Var(model.workshops, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.workshops, domain=pyo.NonNegativeReals)

    model.inspection_excess = pyo.Var(domain=pyo.NonNegativeReals)
    model.mw_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.A_overtime_excess = pyo.Var(domain=pyo.NonNegativeReals)
    model.wh_shortfall = pyo.Var(domain=pyo.NonNegativeReals)

    model.mw_sales_ceiling = pyo.Constraint(
        expr=model.production["mw"] <= demand_mw
    )
    model.wh_sales_ceiling = pyo.Constraint(
        expr=model.production["wh"] <= demand_wh
    )

    model.workshop_A_balance = pyo.Constraint(
        expr=(
            labor_A * model.production["mw"]
            + labor_A_heater * model.production["wh"]
            + model.idle["A"]
            - model.overtime["A"]
            == cap_A
        )
    )
    model.workshop_B_balance = pyo.Constraint(
        expr=(
            assembly_B * model.production["mw"]
            + assembly_B_heater * model.production["wh"]
            + model.idle["B"]
            - model.overtime["B"]
            == cap_B
        )
    )

    model.inspection_goal = pyo.Constraint(
        expr=(
            inspect_cost_mw * model.production["mw"]
            + inspect_cost_wh * model.production["wh"]
            <= inspect_budget + model.inspection_excess
        )
    )
    model.mw_sales_goal = pyo.Constraint(
        expr=model.production["mw"] + model.mw_shortfall >= target_mw
    )
    model.A_overtime_goal = pyo.Constraint(
        expr=(
            model.overtime["A"]
            <= overtime_A_cap + model.A_overtime_excess
        )
    )
    model.wh_sales_goal = pyo.Constraint(
        expr=model.production["wh"] + model.wh_shortfall >= target_wh
    )

    # Hourly-cost weighting preserves the specified workshop cost ratio.
    priority_expressions = [
        model.inspection_excess,
        model.mw_shortfall,
        cost_A * model.idle["A"] + cost_B * model.idle["B"],
        model.A_overtime_excess,
        model.wh_shortfall,
    ]

    model.objective = pyo.Objective(
        expr=priority_expressions[0],
        sense=pyo.minimize,
    )
    model.priority_locks = pyo.ConstraintList()

    # Solve priorities sequentially, preserving every higher-priority optimum.
    for priority_index, expression in enumerate(priority_expressions):
        model.objective.set_value(expression)

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solve_failed"}

        # Success is determined solely by retrieving the objective value.
        try:
            obj_val = float(pyo.value(model.objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_index < len(priority_expressions) - 1:
            model.priority_locks.add(expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}
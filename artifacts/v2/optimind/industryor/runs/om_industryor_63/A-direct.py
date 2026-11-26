import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: production quantities and overtime hours
    model.x_mw = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_wh = pyo.Var(domain=pyo.NonNegativeReals)
    model.ot_A = pyo.Var(domain=pyo.NonNegativeReals)
    model.ot_B = pyo.Var(domain=pyo.NonNegativeReals)

    # Objective: minimize total cost (workshop hours including overtime + inspection/sales)
    model.obj = pyo.Objective(
        expr=(
            params["workshop_A_hour_cost"] * (
                params["microwave_processing_hours_A"] * model.x_mw
                + params["water_heater_processing_hours_A"] * model.x_wh
                + model.ot_A
            )
            + params["workshop_B_hour_cost"] * (
                params["microwave_assembly_hours_B"] * model.x_mw
                + params["water_heater_assembly_hours_B"] * model.x_wh
                + model.ot_B
            )
            + params["inspection_sales_cost_microwave"] * model.x_mw
            + params["inspection_sales_cost_water_heater"] * model.x_wh
        ),
        sense=pyo.minimize,
    )

    # Constraint 1: inspection and sales cost budget
    model.budget = pyo.Constraint(
        expr=(
            params["inspection_sales_cost_microwave"] * model.x_mw
            + params["inspection_sales_cost_water_heater"] * model.x_wh
            <= params["inspection_sales_budget"]
        )
    )

    # Constraints 2 & 5: minimum sales; sales caps
    model.min_mw = pyo.Constraint(expr=model.x_mw >= params["min_sales_microwave"])
    model.max_mw = pyo.Constraint(expr=model.x_mw <= params["max_sales_microwave"])
    model.min_wh = pyo.Constraint(expr=model.x_wh >= params["min_sales_water_heater"])
    model.max_wh = pyo.Constraint(expr=model.x_wh <= params["max_sales_water_heater"])

    # Constraint 3: workshops' regular hours must be fully utilized (overtime >= 0)
    model.workshop_A = pyo.Constraint(
        expr=(
            params["microwave_processing_hours_A"] * model.x_mw
            + params["water_heater_processing_hours_A"] * model.x_wh
            - params["workshop_A_hours_available"]
            == model.ot_A
        )
    )
    model.workshop_B = pyo.Constraint(
        expr=(
            params["microwave_assembly_hours_B"] * model.x_mw
            + params["water_heater_assembly_hours_B"] * model.x_wh
            - params["workshop_B_hours_available"]
            == model.ot_B
        )
    )

    # Constraint 4: overtime cap for workshop A
    model.ot_A_cap = pyo.Constraint(expr=model.ot_A <= params["workshop_A_overtime_cap"])

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
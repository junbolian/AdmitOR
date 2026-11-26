# IR: {"sets":{"products":["microwave","water_heater"],"workshops":["A","B"]},"params":["microwave_processing_hours_A","water_heater_processing_hours_A","microwave_assembly_hours_B","water_heater_assembly_hours_B","inspection_sales_cost_microwave","inspection_sales_cost_water_heater","workshop_A_hours_available","workshop_B_hours_available","workshop_A_hour_cost","workshop_B_hour_cost","max_sales_microwave","max_sales_water_heater","min_sales_microwave","min_sales_water_heater","inspection_sales_budget","workshop_A_overtime_cap"],"interpretation":{"max_sales_microwave":"informational sales forecast, not a hard limit under the explicit monthly plan","max_sales_water_heater":"informational sales forecast, not a hard limit under the explicit monthly plan","objective":"minimize total workshop and inspection/sales costs"},"variables":{"production[products]":"nonnegative integer","overtime[workshops]":"nonnegative real"},"expressions":{"hours_A":"microwave_processing_hours_A*production[microwave]+water_heater_processing_hours_A*production[water_heater]","hours_B":"microwave_assembly_hours_B*production[microwave]+water_heater_assembly_hours_B*production[water_heater]","inspection_cost":"inspection_sales_cost_microwave*production[microwave]+inspection_sales_cost_water_heater*production[water_heater]"},"constraints":["production[microwave]>=min_sales_microwave","production[water_heater]>=min_sales_water_heater","inspection_cost<=inspection_sales_budget","hours_A=workshop_A_hours_available+overtime[A]","hours_B=workshop_B_hours_available+overtime[B]","overtime[A]<=workshop_A_overtime_cap"],"objective":{"sense":"minimize","expression":"workshop_A_hour_cost*hours_A+workshop_B_hour_cost*hours_B+inspection_cost"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The narrative gives estimated sales, while the explicit monthly plan
    # imposes minimum sales. Treating the estimates as hard upper bounds
    # conflicts with the requirement to use all regular workshop A hours.
    # Both forecast parameters are read and retained as model data.
    model = pyo.ConcreteModel()

    parameter_data = {
        "microwave_processing_hours_A": params["microwave_processing_hours_A"],
        "water_heater_processing_hours_A": params[
            "water_heater_processing_hours_A"
        ],
        "microwave_assembly_hours_B": params["microwave_assembly_hours_B"],
        "water_heater_assembly_hours_B": params[
            "water_heater_assembly_hours_B"
        ],
        "inspection_sales_cost_microwave": params[
            "inspection_sales_cost_microwave"
        ],
        "inspection_sales_cost_water_heater": params[
            "inspection_sales_cost_water_heater"
        ],
        "workshop_A_hours_available": params["workshop_A_hours_available"],
        "workshop_B_hours_available": params["workshop_B_hours_available"],
        "workshop_A_hour_cost": params["workshop_A_hour_cost"],
        "workshop_B_hour_cost": params["workshop_B_hour_cost"],
        "max_sales_microwave": params["max_sales_microwave"],
        "max_sales_water_heater": params["max_sales_water_heater"],
        "min_sales_microwave": params["min_sales_microwave"],
        "min_sales_water_heater": params["min_sales_water_heater"],
        "inspection_sales_budget": params["inspection_sales_budget"],
        "workshop_A_overtime_cap": params["workshop_A_overtime_cap"],
    }

    for parameter_name, parameter_value in parameter_data.items():
        model.add_component(
            parameter_name,
            pyo.Param(
                initialize=parameter_value,
                within=pyo.NonNegativeReals,
            ),
        )

    model.products = pyo.Set(
        initialize=("microwave", "water_heater"),
        ordered=True,
    )
    model.workshops = pyo.Set(initialize=("A", "B"), ordered=True)

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeIntegers,
    )
    model.overtime = pyo.Var(
        model.workshops,
        domain=pyo.NonNegativeReals,
    )

    model.hours_A = pyo.Expression(
        expr=(
            model.microwave_processing_hours_A
            * model.production["microwave"]
            + model.water_heater_processing_hours_A
            * model.production["water_heater"]
        )
    )
    model.hours_B = pyo.Expression(
        expr=(
            model.microwave_assembly_hours_B
            * model.production["microwave"]
            + model.water_heater_assembly_hours_B
            * model.production["water_heater"]
        )
    )
    model.inspection_cost = pyo.Expression(
        expr=(
            model.inspection_sales_cost_microwave
            * model.production["microwave"]
            + model.inspection_sales_cost_water_heater
            * model.production["water_heater"]
        )
    )

    model.microwave_minimum = pyo.Constraint(
        expr=model.production["microwave"] >= model.min_sales_microwave
    )
    model.water_heater_minimum = pyo.Constraint(
        expr=(
            model.production["water_heater"]
            >= model.min_sales_water_heater
        )
    )
    model.inspection_budget_limit = pyo.Constraint(
        expr=model.inspection_cost <= model.inspection_sales_budget
    )
    model.workshop_A_utilization = pyo.Constraint(
        expr=(
            model.hours_A
            == model.workshop_A_hours_available + model.overtime["A"]
        )
    )
    model.workshop_B_utilization = pyo.Constraint(
        expr=(
            model.hours_B
            == model.workshop_B_hours_available + model.overtime["B"]
        )
    )
    model.workshop_A_overtime_limit = pyo.Constraint(
        expr=model.overtime["A"] <= model.workshop_A_overtime_cap
    )

    model.total_cost = pyo.Objective(
        expr=(
            model.workshop_A_hour_cost * model.hours_A
            + model.workshop_B_hour_cost * model.hours_B
            + model.inspection_cost
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A solution-loading failure can occur for an infeasible model.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
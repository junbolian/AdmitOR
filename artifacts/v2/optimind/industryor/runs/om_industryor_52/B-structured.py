# IR: {"sets":{"products":[0,1,2],"equipment":["A","B","C"]},"params":{"equipment_hours_per_unit_A":"vector[products]","equipment_hours_per_unit_B":"vector[products]","equipment_hours_per_unit_C":"vector[products]","capacity_A":"scalar","capacity_B":"scalar","capacity_C":"scalar","unit_profit":"vector[products]"},"variables":{"quantity[products]":"nonnegative integer"},"constraints":["For each equipment e: sum(equipment_hours_per_unit_e[j] * quantity[j] for j in products) <= capacity_e"],"objective":{"sense":"maximize","expression":"sum(unit_profit[j] * quantity[j] for j in products)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Maximize monthly profit; input vectors follow product order I, II, III."""
    equipment_hours = {
        "A": params["equipment_hours_per_unit_A"],
        "B": params["equipment_hours_per_unit_B"],
        "C": params["equipment_hours_per_unit_C"],
    }
    capacities = {
        "A": params["capacity_A"],
        "B": params["capacity_B"],
        "C": params["capacity_C"],
    }
    profits = params["unit_profit"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.equipment = pyo.Set(initialize=["A", "B", "C"], ordered=True)

    model.processing_hours = pyo.Param(
        model.equipment,
        model.products,
        initialize=lambda mdl, equipment, product: equipment_hours[equipment][product],
    )
    model.available_hours = pyo.Param(
        model.equipment,
        initialize=capacities,
    )
    model.profit_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: profits[product],
    )

    model.quantity = pyo.Var(
        model.products,
        domain=pyo.NonNegativeIntegers,
    )

    def capacity_rule(mdl, equipment):
        return sum(
            mdl.processing_hours[equipment, product] * mdl.quantity[product]
            for product in mdl.products
        ) <= mdl.available_hours[equipment]

    model.capacity_limits = pyo.Constraint(
        model.equipment,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.quantity[product]
            for product in model.products
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
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
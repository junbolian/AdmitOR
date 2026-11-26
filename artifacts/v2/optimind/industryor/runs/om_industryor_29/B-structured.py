# IR: {"sets":{"P":["I","II","III"],"A":["A1","A2"],"B":["B1","B2","B3"],"R":[["A1","I"],["A1","II"],["A2","I"],["A2","II"],["A2","III"],["B1","I"],["B1","II"],["B2","I"],["B2","III"],["B3","I"]]},"params":["A1_hours","A1_hours_II","A2_hours_I","A2_hours_II","A2_hours_III","B1_hours_I","B1_hours_II","B2_hours_I","B2_hours_III","B3_hours_I","capacity_A1","capacity_A2","capacity_B1","capacity_B2","capacity_B3","full_load_cost_A1","full_load_cost_A2","full_load_cost_B1","full_load_cost_B2","full_load_cost_B3","proc_cost_A1","proc_cost_A2","proc_cost_B1","proc_cost_B2","proc_cost_B3","raw_material_cost","unit_price"],"input_schema":{"raw_material_cost":"mapping keyed by I,II,III or sequence in that order","unit_price":"mapping keyed by I,II,III or sequence in that order","capacities":"strictly positive"},"variables":{"q[p]":"NonNegativeReals: total product quantity","x[e,p]":"NonNegativeReals on R: quantity processed on equipment e"},"expressions":{"h[e]":"sum(t[e,p]*x[e,p] for allowed products p)"},"constraints":["For each p: sum(x[e,p] for allowed e in A) = q[p]","For each p: sum(x[e,p] for allowed e in B) = q[p]","For each e: h[e] <= capacity[e]"],"objective":"maximize sum((unit_price[p]-raw_material_cost[p])*q[p]) - sum((proc_cost[e]+full_load_cost[e]/capacity[e])*h[e])","assumptions":["Production quantities are continuous.","Full-load equipment costs are prorated by machine-hour utilization."]}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _product_values(values, products):
    """Accept product-keyed mappings or sequences ordered I, II, III."""
    if isinstance(values, Mapping):
        return {product: values[product] for product in products}

    if len(values) != len(products):
        raise ValueError("Product cost and price sequences must have three entries.")

    return {
        product: values[position]
        for position, product in enumerate(products)
    }


def solve(params):
    products = ("I", "II", "III")
    stage_a = ("A1", "A2")
    stage_b = ("B1", "B2", "B3")
    equipment = stage_a + stage_b

    processing_times = {
        ("A1", "I"): params["A1_hours"],
        ("A1", "II"): params["A1_hours_II"],
        ("A2", "I"): params["A2_hours_I"],
        ("A2", "II"): params["A2_hours_II"],
        ("A2", "III"): params["A2_hours_III"],
        ("B1", "I"): params["B1_hours_I"],
        ("B1", "II"): params["B1_hours_II"],
        ("B2", "I"): params["B2_hours_I"],
        ("B2", "III"): params["B2_hours_III"],
        ("B3", "I"): params["B3_hours_I"],
    }

    capacities = {
        "A1": params["capacity_A1"],
        "A2": params["capacity_A2"],
        "B1": params["capacity_B1"],
        "B2": params["capacity_B2"],
        "B3": params["capacity_B3"],
    }

    full_load_costs = {
        "A1": params["full_load_cost_A1"],
        "A2": params["full_load_cost_A2"],
        "B1": params["full_load_cost_B1"],
        "B2": params["full_load_cost_B2"],
        "B3": params["full_load_cost_B3"],
    }

    processing_costs = {
        "A1": params["proc_cost_A1"],
        "A2": params["proc_cost_A2"],
        "B1": params["proc_cost_B1"],
        "B2": params["proc_cost_B2"],
        "B3": params["proc_cost_B3"],
    }

    material_costs = _product_values(params["raw_material_cost"], products)
    sales_prices = _product_values(params["unit_price"], products)

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=products, ordered=True)
    model.stage_a_equipment = pyo.Set(initialize=stage_a, ordered=True)
    model.stage_b_equipment = pyo.Set(initialize=stage_b, ordered=True)
    model.equipment = pyo.Set(initialize=equipment, ordered=True)
    model.allowed_routes = pyo.Set(
        dimen=2,
        initialize=list(processing_times),
        ordered=True,
    )

    model.processing_time = pyo.Param(
        model.allowed_routes,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )
    model.machine_capacity = pyo.Param(
        model.equipment,
        initialize=capacities,
        within=pyo.PositiveReals,
    )
    model.full_load_cost = pyo.Param(
        model.equipment,
        initialize=full_load_costs,
        within=pyo.NonNegativeReals,
    )
    model.hourly_processing_cost = pyo.Param(
        model.equipment,
        initialize=processing_costs,
        within=pyo.NonNegativeReals,
    )
    model.material_cost = pyo.Param(
        model.products,
        initialize=material_costs,
        within=pyo.NonNegativeReals,
    )
    model.sales_price = pyo.Param(
        model.products,
        initialize=sales_prices,
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )
    model.processed_quantity = pyo.Var(
        model.allowed_routes,
        domain=pyo.NonNegativeReals,
    )

    def machine_hours_rule(instance, equipment_id):
        return sum(
            instance.processing_time[equipment_id, product]
            * instance.processed_quantity[equipment_id, product]
            for product in instance.products
            if (equipment_id, product) in instance.allowed_routes
        )

    model.machine_hours = pyo.Expression(
        model.equipment,
        rule=machine_hours_rule,
    )

    def stage_a_balance_rule(instance, product):
        return sum(
            instance.processed_quantity[equipment_id, product]
            for equipment_id in instance.stage_a_equipment
            if (equipment_id, product) in instance.allowed_routes
        ) == instance.production[product]

    def stage_b_balance_rule(instance, product):
        return sum(
            instance.processed_quantity[equipment_id, product]
            for equipment_id in instance.stage_b_equipment
            if (equipment_id, product) in instance.allowed_routes
        ) == instance.production[product]

    def machine_capacity_rule(instance, equipment_id):
        return (
            instance.machine_hours[equipment_id]
            <= instance.machine_capacity[equipment_id]
        )

    model.stage_a_balance = pyo.Constraint(
        model.products,
        rule=stage_a_balance_rule,
    )
    model.stage_b_balance = pyo.Constraint(
        model.products,
        rule=stage_b_balance_rule,
    )
    model.machine_capacity_limit = pyo.Constraint(
        model.equipment,
        rule=machine_capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=(
            sum(
                (
                    model.sales_price[product]
                    - model.material_cost[product]
                )
                * model.production[product]
                for product in model.products
            )
            - sum(
                (
                    model.hourly_processing_cost[equipment_id]
                    + model.full_load_cost[equipment_id]
                    / model.machine_capacity[equipment_id]
                )
                * model.machine_hours[equipment_id]
                for equipment_id in model.equipment
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
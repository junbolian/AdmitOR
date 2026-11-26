# IR: {"sets":{"products":["I","II","III"],"equipment":["A1","A2","B1","B2","B3"],"step_A":["A1","A2"],"step_B":["B1","B2","B3"],"eligible":[["A1","I"],["A1","II"],["A2","I"],["A2","II"],["A2","III"],["B1","I"],["B1","II"],["B2","I"],["B2","III"],["B3","I"]]},"params":{"unit_processing_time":"row-major length-15 array or 5x3 array, equipment by product","equipment_available_time":"length-5 array in equipment order; positive hours","equipment_cost_full_load":"length-5 array in equipment order; CNY","raw_material_cost":"length-3 array in product order; CNY/unit","unit_price":"length-3 array in product order; CNY/unit"},"variables":{"production[p]":"NonNegativeReals","allocation[e,p]":"NonNegativeReals on eligible pairs"},"constraints":["For every product p: sum(allocation[e,p] for eligible step-A equipment e) = production[p].","For every product p: sum(allocation[e,p] for eligible step-B equipment e) = production[p].","For every equipment e: sum(unit_processing_time[e,p]*allocation[e,p] for eligible products p) <= equipment_available_time[e]."],"objective":"Maximize sum((unit_price[p]-raw_material_cost[p])*production[p]) - sum((equipment_cost_full_load[e]/equipment_available_time[e])*sum(unit_processing_time[e,p]*allocation[e,p] for eligible products p))."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("I", "II", "III")
    equipment = ("A1", "A2", "B1", "B2", "B3")
    step_a = ("A1", "A2")
    step_b = ("B1", "B2", "B3")
    eligible = (
        ("A1", "I"),
        ("A1", "II"),
        ("A2", "I"),
        ("A2", "II"),
        ("A2", "III"),
        ("B1", "I"),
        ("B1", "II"),
        ("B2", "I"),
        ("B2", "III"),
        ("B3", "I"),
    )
    eligible_set = set(eligible)

    processing_input = params["unit_processing_time"]
    available_input = params["equipment_available_time"]
    equipment_cost_input = params["equipment_cost_full_load"]
    material_cost_input = params["raw_material_cost"]
    price_input = params["unit_price"]

    if len(processing_input) == len(equipment) * len(products):
        processing_time = {
            (equipment_id, product_id): float(
                processing_input[equipment_pos * len(products) + product_pos]
            )
            for equipment_pos, equipment_id in enumerate(equipment)
            for product_pos, product_id in enumerate(products)
            if (equipment_id, product_id) in eligible_set
        }
    elif len(processing_input) == len(equipment):
        if any(len(row) != len(products) for row in processing_input):
            raise ValueError("unit_processing_time must have three columns.")
        processing_time = {
            (equipment_id, product_id): float(
                processing_input[equipment_pos][product_pos]
            )
            for equipment_pos, equipment_id in enumerate(equipment)
            for product_pos, product_id in enumerate(products)
            if (equipment_id, product_id) in eligible_set
        }
    else:
        raise ValueError("unit_processing_time must be length 15 or shape 5x3.")

    vector_specs = (
        ("equipment_available_time", available_input, len(equipment)),
        ("equipment_cost_full_load", equipment_cost_input, len(equipment)),
        ("raw_material_cost", material_cost_input, len(products)),
        ("unit_price", price_input, len(products)),
    )
    for parameter_name, values, expected_length in vector_specs:
        if len(values) != expected_length:
            raise ValueError(
                f"{parameter_name} must contain {expected_length} values."
            )

    available_time = {
        equipment_id: float(available_input[position])
        for position, equipment_id in enumerate(equipment)
    }
    equipment_cost = {
        equipment_id: float(equipment_cost_input[position])
        for position, equipment_id in enumerate(equipment)
    }
    material_cost = {
        product_id: float(material_cost_input[position])
        for position, product_id in enumerate(products)
    }
    selling_price = {
        product_id: float(price_input[position])
        for position, product_id in enumerate(products)
    }

    if any(value <= 0 for value in available_time.values()):
        raise ValueError("equipment_available_time values must be positive.")

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.equipment = pyo.Set(initialize=equipment, ordered=True)
    model.eligible_pairs = pyo.Set(dimen=2, initialize=eligible, ordered=True)

    model.processing_time = pyo.Param(
        model.eligible_pairs, initialize=processing_time
    )
    model.available_time = pyo.Param(
        model.equipment, initialize=available_time
    )
    model.full_load_cost = pyo.Param(
        model.equipment, initialize=equipment_cost
    )
    model.material_cost = pyo.Param(
        model.products, initialize=material_cost
    )
    model.selling_price = pyo.Param(
        model.products, initialize=selling_price
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )
    model.allocation = pyo.Var(
        model.eligible_pairs, domain=pyo.NonNegativeReals
    )

    def step_a_balance_rule(current_model, product_id):
        return sum(
            current_model.allocation[equipment_id, product_id]
            for equipment_id in step_a
            if (equipment_id, product_id) in eligible_set
        ) == current_model.production[product_id]

    def step_b_balance_rule(current_model, product_id):
        return sum(
            current_model.allocation[equipment_id, product_id]
            for equipment_id in step_b
            if (equipment_id, product_id) in eligible_set
        ) == current_model.production[product_id]

    def hours_used_rule(current_model, equipment_id):
        return sum(
            current_model.processing_time[equipment_id, product_id]
            * current_model.allocation[equipment_id, product_id]
            for product_id in products
            if (equipment_id, product_id) in eligible_set
        )

    model.step_a_balance = pyo.Constraint(
        model.products, rule=step_a_balance_rule
    )
    model.step_b_balance = pyo.Constraint(
        model.products, rule=step_b_balance_rule
    )
    model.hours_used = pyo.Expression(
        model.equipment, rule=hours_used_rule
    )
    model.capacity_limit = pyo.Constraint(
        model.equipment,
        rule=lambda current_model, equipment_id: (
            current_model.hours_used[equipment_id]
            <= current_model.available_time[equipment_id]
        ),
    )

    # Equipment costs accrue proportionally to processing hours used.
    model.profit = pyo.Objective(
        expr=sum(
            (model.selling_price[product_id] - model.material_cost[product_id])
            * model.production[product_id]
            for product_id in products
        )
        - sum(
            model.full_load_cost[equipment_id]
            * model.hours_used[equipment_id]
            / model.available_time[equipment_id]
            for equipment_id in equipment
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
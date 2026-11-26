# IR: {"sets":{"P":["I","II","III"],"A":["A1","A2"],"B":["B1","B2","B3"],"R":[["A1","I"],["A2","I"],["B1","I"],["B2","I"],["B3","I"],["A1","II"],["A2","II"],["B1","II"],["A2","III"],["B2","III"]]},"params":["processing_time[machine,product]","effective_hours[machine]","machine_fee[machine]","raw_material_cost[product]","selling_price[product]"],"variables":{"quantity[product]":"NonNegativeReals","processed[machine,product] for (machine,product) in R":"NonNegativeReals"},"constraints":["For each product: sum(processed[machine,product] over eligible A machines) = quantity[product].","For each product: sum(processed[machine,product] over eligible B machines) = quantity[product].","For each machine: sum(processing_time[machine,product]*processed[machine,product] over eligible products) <= effective_hours[machine]."],"objective":"maximize sum((selling_price[product]-raw_material_cost[product])*quantity[product]) - sum(machine_fee[machine]*processing_time[machine,product]*processed[machine,product])","interpretation":"Resolve contradictory prose using the table's populated B-stage cells: product II uses B1, not the blank B2-II cell. Product II may use either A machine. Product III uses only A2 and B2. Product I may use all machines. No missing processing time is inferred or hardcoded."}

import math
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


PRODUCTS = ("I", "II", "III")
A_MACHINES = ("A1", "A2")
B_MACHINES = ("B1", "B2", "B3")
MACHINES = A_MACHINES + B_MACHINES

ROUTES = (
    ("A1", "I"),
    ("A2", "I"),
    ("B1", "I"),
    ("B2", "I"),
    ("B3", "I"),
    ("A1", "II"),
    ("A2", "II"),
    ("B1", "II"),
    ("A2", "III"),
    ("B2", "III"),
)


# Accepted input layouts:
# Machine vectors: mappings keyed by MACHINES, or sequences in MACHINES order.
# Product vectors: mappings keyed by PRODUCTS, or sequences in PRODUCTS order.
# processing_time: mapping keyed by (machine, product), nested machine/product
# mappings, or a matrix in MACHINES-row and PRODUCTS-column order.
# Nested machine rows may also be sequences in PRODUCTS order.
# Only processing times for ROUTES are required.


def _vector_entry(data, label, labels):
    if isinstance(data, Mapping):
        return data[label]
    return data[labels.index(label)]


def _processing_entry(data, machine, product):
    if isinstance(data, Mapping):
        if (machine, product) in data:
            return data[(machine, product)]
        row = data[machine]
    else:
        row = data[MACHINES.index(machine)]
    return _vector_entry(row, product, PRODUCTS)


def _finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Parameter values must be finite.")
    return result


def solve(params):
    try:
        processing_input = params["processing_time"]
        hours_input = params["effective_hours"]
        fee_input = params["machine_fee"]
        material_input = params["raw_material_cost"]
        price_input = params["selling_price"]

        processing = {
            (machine, product): _finite_float(
                _processing_entry(processing_input, machine, product)
            )
            for machine, product in ROUTES
        }
        hours = {
            machine: _finite_float(
                _vector_entry(hours_input, machine, MACHINES)
            )
            for machine in MACHINES
        }
        fees = {
            machine: _finite_float(
                _vector_entry(fee_input, machine, MACHINES)
            )
            for machine in MACHINES
        }
        material_costs = {
            product: _finite_float(
                _vector_entry(material_input, product, PRODUCTS)
            )
            for product in PRODUCTS
        }
        prices = {
            product: _finite_float(
                _vector_entry(price_input, product, PRODUCTS)
            )
            for product in PRODUCTS
        }
    except (KeyError, IndexError, TypeError, ValueError, OverflowError):
        return {"objective": None, "status": "invalid_or_missing_parameters"}

    if (
        any(value <= 0 for value in processing.values())
        or any(value < 0 for value in hours.values())
        or any(value < 0 for value in fees.values())
        or any(value < 0 for value in material_costs.values())
        or any(value < 0 for value in prices.values())
    ):
        return {"objective": None, "status": "invalid_parameter_values"}

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=PRODUCTS, ordered=True)
    model.a_machines = pyo.Set(initialize=A_MACHINES, ordered=True)
    model.b_machines = pyo.Set(initialize=B_MACHINES, ordered=True)
    model.machines = pyo.Set(initialize=MACHINES, ordered=True)
    model.routes = pyo.Set(initialize=ROUTES, dimen=2, ordered=True)

    model.processing_time = pyo.Param(
        model.routes, initialize=processing, within=pyo.PositiveReals
    )
    model.effective_hours = pyo.Param(
        model.machines, initialize=hours, within=pyo.NonNegativeReals
    )
    model.machine_fee = pyo.Param(
        model.machines, initialize=fees, within=pyo.NonNegativeReals
    )
    model.raw_material_cost = pyo.Param(
        model.products, initialize=material_costs, within=pyo.NonNegativeReals
    )
    model.selling_price = pyo.Param(
        model.products, initialize=prices, within=pyo.NonNegativeReals
    )

    model.quantity = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.processed = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def stage_a_rule(current_model, product):
        return (
            sum(
                current_model.processed[machine, product]
                for machine in A_MACHINES
                if (machine, product) in current_model.routes
            )
            == current_model.quantity[product]
        )

    def stage_b_rule(current_model, product):
        return (
            sum(
                current_model.processed[machine, product]
                for machine in B_MACHINES
                if (machine, product) in current_model.routes
            )
            == current_model.quantity[product]
        )

    def capacity_rule(current_model, machine):
        return (
            sum(
                current_model.processing_time[machine, product]
                * current_model.processed[machine, product]
                for product in PRODUCTS
                if (machine, product) in current_model.routes
            )
            <= current_model.effective_hours[machine]
        )

    model.stage_a_balance = pyo.Constraint(
        model.products, rule=stage_a_rule
    )
    model.stage_b_balance = pyo.Constraint(
        model.products, rule=stage_b_rule
    )
    model.machine_capacity = pyo.Constraint(
        model.machines, rule=capacity_rule
    )

    model.profit = pyo.Objective(
        expr=sum(
            (
                model.selling_price[product]
                - model.raw_material_cost[product]
            )
            * model.quantity[product]
            for product in PRODUCTS
        )
        - sum(
            model.machine_fee[machine]
            * model.processing_time[machine, product]
            * model.processed[machine, product]
            for machine, product in ROUTES
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
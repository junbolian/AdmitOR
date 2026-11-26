# IR: {"sets":{"products":["I","II","III"],"machines":["A1","A2","B1","B2","B3"],"stages":{"A":["A1","A2"],"B":["B1","B2","B3"]},"eligible_machines":{"I":["A1","A2","B1","B2","B3"],"II":["A1","A2","B1"],"III":["A2","B2"]},"arcs":"Eligible product-machine pairs with present, nonblank processing times."},"params":{"processing_time_I":"Machine-keyed mapping, five-machine sequence, or eligible-machine sequence.","processing_time_II":"Machine-keyed mapping, five-machine sequence, or eligible-machine sequence.","processing_time_III":"Machine-keyed mapping, five-machine sequence, or eligible-machine sequence.","effective_hours":"Machine-keyed mapping or sequence in machines order; positive.","operating_cost_full":"Machine-keyed mapping or sequence in machines order; nonnegative.","raw_material_cost":"Product-keyed mapping or sequence in products order; nonnegative.","unit_price":"Product-keyed mapping or sequence in products order; nonnegative."},"variables":{"production[p]":"NonNegativeReals","processed[p,e]":"NonNegativeReals on arcs"},"constraints":["For each product p and stage s: sum(processed[p,e] over applicable machines e in s) = production[p].","For each machine e: sum(processing_time[p,e]*processed[p,e] over applicable products p) <= effective_hours[e]."],"objective":"Maximize sum((unit_price[p]-raw_material_cost[p])*production[p]) - sum(operating_cost_full[e]*machine_load[e]/effective_hours[e]); operating costs are proportional to utilized capacity."}

from collections.abc import Mapping, Sequence

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _as_mapping(values, ordered_keys, label, eligible_keys=None):
    """Accept keyed inputs or positional inputs with documented ordering."""
    if isinstance(values, Mapping):
        return dict(values)

    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise TypeError(f"{label} must be a mapping or a sequence.")

    if len(values) == len(ordered_keys):
        return dict(zip(ordered_keys, values))

    if eligible_keys is not None and len(values) == len(eligible_keys):
        return dict(zip(eligible_keys, values))

    expected_lengths = {len(ordered_keys)}
    if eligible_keys is not None:
        expected_lengths.add(len(eligible_keys))

    expected = " or ".join(str(length) for length in sorted(expected_lengths))
    raise ValueError(f"{label} must contain {expected} entries.")


def solve(params):
    products = ("I", "II", "III")
    machines = ("A1", "A2", "B1", "B2", "B3")
    stages = {
        "A": ("A1", "A2"),
        "B": ("B1", "B2", "B3"),
    }
    eligible_machines = {
        "I": ("A1", "A2", "B1", "B2", "B3"),
        "II": ("A1", "A2", "B1"),
        "III": ("A2", "B2"),
    }

    processing_inputs = {
        "I": params["processing_time_I"],
        "II": params["processing_time_II"],
        "III": params["processing_time_III"],
    }
    hours_input = _as_mapping(
        params["effective_hours"], machines, "effective_hours"
    )
    operating_cost_input = _as_mapping(
        params["operating_cost_full"], machines, "operating_cost_full"
    )
    material_cost_input = _as_mapping(
        params["raw_material_cost"], products, "raw_material_cost"
    )
    price_input = _as_mapping(
        params["unit_price"], products, "unit_price"
    )

    processing_times = {}
    for product in products:
        entries = _as_mapping(
            processing_inputs[product],
            machines,
            f"processing_time_{product}",
            eligible_keys=eligible_machines[product],
        )
        for machine in eligible_machines[product]:
            value = entries.get(machine)
            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                continue
            processing_times[product, machine] = float(value)

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.machines = pyo.Set(initialize=machines, ordered=True)
    model.stages = pyo.Set(initialize=tuple(stages), ordered=True)
    model.processing_arcs = pyo.Set(
        dimen=2,
        initialize=tuple(processing_times),
        ordered=True,
    )

    model.processing_time = pyo.Param(
        model.processing_arcs,
        initialize=processing_times,
        within=pyo.PositiveReals,
    )
    model.effective_hours = pyo.Param(
        model.machines,
        initialize={
            machine: float(hours_input[machine])
            for machine in machines
        },
        within=pyo.PositiveReals,
    )
    model.operating_cost_full = pyo.Param(
        model.machines,
        initialize={
            machine: float(operating_cost_input[machine])
            for machine in machines
        },
        within=pyo.NonNegativeReals,
    )
    model.raw_material_cost = pyo.Param(
        model.products,
        initialize={
            product: float(material_cost_input[product])
            for product in products
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_price = pyo.Param(
        model.products,
        initialize={
            product: float(price_input[product])
            for product in products
        },
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )
    model.processed = pyo.Var(
        model.processing_arcs,
        domain=pyo.NonNegativeReals,
    )

    def stage_balance_rule(factory, product, stage):
        return sum(
            factory.processed[product, machine]
            for machine in stages[stage]
            if (product, machine) in factory.processing_arcs
        ) == factory.production[product]

    model.stage_balance = pyo.Constraint(
        model.products,
        model.stages,
        rule=stage_balance_rule,
    )

    def machine_load_rule(factory, machine):
        return sum(
            factory.processing_time[product, machine]
            * factory.processed[product, machine]
            for product in factory.products
            if (product, machine) in factory.processing_arcs
        )

    model.machine_load = pyo.Expression(
        model.machines,
        rule=machine_load_rule,
    )

    def capacity_rule(factory, machine):
        return (
            factory.machine_load[machine]
            <= factory.effective_hours[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            (
                model.unit_price[product]
                - model.raw_material_cost[product]
            )
            * model.production[product]
            for product in model.products
        )
        - sum(
            model.operating_cost_full[machine]
            * model.machine_load[machine]
            / model.effective_hours[machine]
            for machine in model.machines
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Preserve unexpected solver exceptions.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"products":[1,2,3],"positions":[1,2,3],"machines":[1,2,3]},"params":{"t_11":"nonnegative processing time","t_12":"nonnegative processing time","t_13":"nonnegative processing time","t_21":"nonnegative processing time","t_22":"nonnegative processing time","t_23":"nonnegative processing time","t_31":"nonnegative processing time","t_32":"nonnegative processing time","t_33":"nonnegative processing time"},"variables":{"assignment[i,r]":"binary; product i occupies position r on every machine","completion[r,j]":"nonnegative continuous; completion of position r on machine j"},"expressions":{"duration[r,j]":"sum_i t_ij * assignment[i,r]"},"constraints":["Each product occupies exactly one position: sum_r assignment[i,r] = 1.","Each position contains exactly one product: sum_i assignment[i,r] = 1.","Machine sequence: completion[r,j] >= (completion[r-1,j] if r>1 else 0) + duration[r,j].","Machine routing: completion[r,j] >= completion[r,j-1] + duration[r,j] for j>1."],"objective":{"sense":"minimize","expression":"completion[3,3]","meaning":"makespan"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(1, 3)
    model.positions = pyo.RangeSet(1, 3)
    model.machines = pyo.RangeSet(1, 3)

    processing_times = {
        (1, 1): params["t_11"],
        (1, 2): params["t_12"],
        (1, 3): params["t_13"],
        (2, 1): params["t_21"],
        (2, 2): params["t_22"],
        (2, 3): params["t_23"],
        (3, 1): params["t_31"],
        (3, 2): params["t_32"],
        (3, 3): params["t_33"],
    }

    model.processing_time = pyo.Param(
        model.products,
        model.machines,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.products, model.positions, domain=pyo.Binary
    )
    model.completion = pyo.Var(
        model.positions, model.machines, domain=pyo.NonNegativeReals
    )

    def duration_rule(mdl, position, machine):
        return sum(
            mdl.processing_time[product, machine]
            * mdl.assignment[product, position]
            for product in mdl.products
        )

    model.duration = pyo.Expression(
        model.positions, model.machines, rule=duration_rule
    )

    def product_position_rule(mdl, product):
        return sum(
            mdl.assignment[product, position]
            for position in mdl.positions
        ) == 1

    model.product_position = pyo.Constraint(
        model.products, rule=product_position_rule
    )

    def position_product_rule(mdl, position):
        return sum(
            mdl.assignment[product, position]
            for product in mdl.products
        ) == 1

    model.position_product = pyo.Constraint(
        model.positions, rule=position_product_rule
    )

    def machine_sequence_rule(mdl, position, machine):
        previous_completion = (
            mdl.completion[position - 1, machine]
            if position > 1
            else 0
        )
        return (
            mdl.completion[position, machine]
            >= previous_completion + mdl.duration[position, machine]
        )

    model.machine_sequence = pyo.Constraint(
        model.positions, model.machines, rule=machine_sequence_rule
    )

    def machine_routing_rule(mdl, position, machine):
        if machine == 1:
            return pyo.Constraint.Skip
        return (
            mdl.completion[position, machine]
            >= mdl.completion[position, machine - 1]
            + mdl.duration[position, machine]
        )

    model.machine_routing = pyo.Constraint(
        model.positions, model.machines, rule=machine_routing_rule
    )

    model.makespan = pyo.Objective(
        expr=model.completion[3, 3],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.makespan))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
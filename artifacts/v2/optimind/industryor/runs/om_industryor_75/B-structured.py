# IR: {"sets":{"I":[1,2,3,4,5,6,7,8,9,10],"J":["A","B","C"]},"params":{"c[i,A]":"processing_cost_A[i]","c[i,B]":"processing_cost_B[i]","c[i,C]":"processing_cost_C[i]","d[A]":"setup_cost_A","d[B]":"setup_cost_B","d[C]":"setup_cost_C","K":"max_parts_on_C"},"variables":{"x[i,j]":"binary; part i assigned to machine j","y[j]":"binary; machine j used"},"constraints":["sum(j in J) x[i,j] = 1 for each i in I","x[i,j] <= y[j] for each i in I,j in J","y[j] <= sum(i in I) x[i,j] for each j in J","x[1,A] + x[2,A] = 1","x[3,A] = 1","x[4,B] = 1","x[5,C] = 1","sum(i in I) x[i,C] <= K"],"objective":"minimize sum(i in I,j in J) c[i,j]*x[i,j] + sum(j in J) d[j]*y[j]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Cost vectors may be length-10 sequences or mappings keyed by part number."""

    cost_inputs = {
        "A": params["processing_cost_A"],
        "B": params["processing_cost_B"],
        "C": params["processing_cost_C"],
    }
    setup_inputs = {
        "A": params["setup_cost_A"],
        "B": params["setup_cost_B"],
        "C": params["setup_cost_C"],
    }
    capacity_input = params["max_parts_on_C"]

    def part_cost(values, part):
        if isinstance(values, Mapping):
            if part in values:
                return values[part]
            return values[str(part)]
        if len(values) != 10:
            raise ValueError("Each processing-cost sequence must have 10 entries.")
        return values[part - 1]

    model = pyo.ConcreteModel()
    model.parts = pyo.RangeSet(1, 10)
    model.machines = pyo.Set(initialize=("A", "B", "C"), ordered=True)

    model.processing_cost = pyo.Param(
        model.parts,
        model.machines,
        initialize={
            (part, machine): part_cost(cost_inputs[machine], part)
            for part in model.parts
            for machine in model.machines
        },
        within=pyo.Reals,
    )
    model.setup_cost = pyo.Param(
        model.machines,
        initialize=setup_inputs,
        within=pyo.Reals,
    )
    model.c_capacity = pyo.Param(
        initialize=capacity_input,
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.parts, model.machines, domain=pyo.Binary
    )
    model.machine_used = pyo.Var(model.machines, domain=pyo.Binary)

    def assign_once_rule(instance, part):
        return sum(
            instance.assignment[part, machine]
            for machine in instance.machines
        ) == 1

    model.assign_once = pyo.Constraint(
        model.parts, rule=assign_once_rule
    )

    def setup_required_rule(instance, part, machine):
        return (
            instance.assignment[part, machine]
            <= instance.machine_used[machine]
        )

    model.setup_required = pyo.Constraint(
        model.parts, model.machines, rule=setup_required_rule
    )

    def setup_only_when_used_rule(instance, machine):
        return instance.machine_used[machine] <= sum(
            instance.assignment[part, machine]
            for part in instance.parts
        )

    model.setup_only_when_used = pyo.Constraint(
        model.machines, rule=setup_only_when_used_rule
    )

    model.first_second_logic = pyo.Constraint(
        expr=model.assignment[1, "A"] + model.assignment[2, "A"] == 1
    )
    model.part_three_required = pyo.Constraint(
        expr=model.assignment[3, "A"] == 1
    )
    model.part_four_required = pyo.Constraint(
        expr=model.assignment[4, "B"] == 1
    )
    model.part_five_required = pyo.Constraint(
        expr=model.assignment[5, "C"] == 1
    )
    model.machine_c_limit = pyo.Constraint(
        expr=sum(
            model.assignment[part, "C"] for part in model.parts
        ) <= model.c_capacity
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.processing_cost[part, machine]
            * model.assignment[part, machine]
            for part in model.parts
            for machine in model.machines
        )
        + sum(
            model.setup_cost[machine] * model.machine_used[machine]
            for machine in model.machines
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
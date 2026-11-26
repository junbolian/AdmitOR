# IR:
# {
#   "sets": {"parts": [1,2,3,4,5,6,7,8,9,10], "equipment": ["A","B","C"]},
#   "params": {
#     "setup_cost_A": "setup cost for A",
#     "setup_cost_B": "setup cost for B",
#     "setup_cost_C": "setup cost for C",
#     "processing_cost_A": "10-element sequence; entry i-1 is A's cost for part i",
#     "processing_cost_B": "10-element sequence; entry i-1 is B's cost for part i",
#     "processing_cost_C": "10-element sequence; entry i-1 is C's cost for part i",
#     "max_parts_on_C": "maximum number of parts assigned to C"
#   },
#   "variables": {"x[i,e]": "binary assignment", "y[e]": "binary equipment usage"},
#   "constraints": [
#     "sum(e in equipment, x[i,e]) = 1 for every part i",
#     "x[i,e] <= y[e] for every part i and equipment e",
#     "y[e] <= sum(i in parts, x[i,e]) for every equipment e",
#     "x[1,A] + x[2,A] = 1",
#     "x[3,A] = 1",
#     "x[4,B] = 1",
#     "x[5,C] = 1",
#     "sum(i in parts, x[i,C]) <= max_parts_on_C"
#   ],
#   "objective": "minimize sum(e, setup_cost[e]*y[e]) + sum(i,e, processing_cost[i,e]*x[i,e])"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    setup_costs = {
        "A": params["setup_cost_A"],
        "B": params["setup_cost_B"],
        "C": params["setup_cost_C"],
    }
    processing_costs = {
        "A": params["processing_cost_A"],
        "B": params["processing_cost_B"],
        "C": params["processing_cost_C"],
    }
    capacity_c = params["max_parts_on_C"]

    for equipment in ("A", "B", "C"):
        if len(processing_costs[equipment]) != 10:
            raise ValueError(
                f"processing_cost_{equipment} must contain exactly 10 entries."
            )

    model = pyo.ConcreteModel()

    model.parts = pyo.RangeSet(1, 10)
    model.equipment = pyo.Set(initialize=("A", "B", "C"), ordered=True)

    model.setup_cost = pyo.Param(
        model.equipment,
        initialize=setup_costs,
        within=pyo.Reals,
    )
    model.processing_cost = pyo.Param(
        model.parts,
        model.equipment,
        initialize={
            (part, equipment): processing_costs[equipment][part - 1]
            for part in model.parts
            for equipment in model.equipment
        },
        within=pyo.Reals,
    )
    model.capacity_c = pyo.Param(initialize=capacity_c, within=pyo.Reals)

    model.x = pyo.Var(model.parts, model.equipment, domain=pyo.Binary)
    model.y = pyo.Var(model.equipment, domain=pyo.Binary)

    def assignment_rule(instance, part):
        return sum(
            instance.x[part, equipment] for equipment in instance.equipment
        ) == 1

    model.assignment = pyo.Constraint(model.parts, rule=assignment_rule)

    def setup_required_rule(instance, part, equipment):
        return instance.x[part, equipment] <= instance.y[equipment]

    model.setup_required = pyo.Constraint(
        model.parts,
        model.equipment,
        rule=setup_required_rule,
    )

    def equipment_used_rule(instance, equipment):
        return instance.y[equipment] <= sum(
            instance.x[part, equipment] for part in instance.parts
        )

    model.equipment_used = pyo.Constraint(
        model.equipment,
        rule=equipment_used_rule,
    )

    model.first_second_requirement = pyo.Constraint(
        expr=model.x[1, "A"] + model.x[2, "A"] == 1
    )
    model.part_three_requirement = pyo.Constraint(expr=model.x[3, "A"] == 1)
    model.part_four_requirement = pyo.Constraint(expr=model.x[4, "B"] == 1)
    model.part_five_requirement = pyo.Constraint(expr=model.x[5, "C"] == 1)

    model.equipment_c_capacity = pyo.Constraint(
        expr=sum(model.x[part, "C"] for part in model.parts) <= model.capacity_c
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.setup_cost[equipment] * model.y[equipment]
                for equipment in model.equipment
            )
            + sum(
                model.processing_cost[part, equipment] * model.x[part, equipment]
                for part in model.parts
                for equipment in model.equipment
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
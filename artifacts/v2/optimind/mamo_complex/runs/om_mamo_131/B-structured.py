# IR: {"sets":{"G":[1,2,3],"N":["A","B","C","D"]},"params":{"cost[g]":["cost_grain1","cost_grain2","cost_grain3"],"nutrient[A,g]":["nutrient_A_grain1","nutrient_A_grain2","nutrient_A_grain3"],"nutrient[B,g]":["nutrient_B_grain1","nutrient_B_grain2","nutrient_B_grain3"],"nutrient[C,g]":["nutrient_C_grain1","nutrient_C_grain2","nutrient_C_grain3"],"nutrient[D,g]":["nutrient_D_grain1","nutrient_D_grain2","nutrient_D_grain3"],"requirement[n]":["req_A","req_B","req_C","req_D"]},"variables":{"x[g]":{"type":"continuous","domain":"nonnegative","units":"pounds per sheep per day"}},"constraints":["For each n in N: sum(nutrient[n,g]*x[g] for g in G) >= requirement[n]"],"objective":{"sense":"minimize","expression":"sum(cost[g]*x[g] for g in G)","units":"cents per sheep per day"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    grains = (1, 2, 3)
    nutrients = ("A", "B", "C", "D")

    cost_data = {
        1: params["cost_grain1"],
        2: params["cost_grain2"],
        3: params["cost_grain3"],
    }
    nutrient_data = {
        ("A", 1): params["nutrient_A_grain1"],
        ("A", 2): params["nutrient_A_grain2"],
        ("A", 3): params["nutrient_A_grain3"],
        ("B", 1): params["nutrient_B_grain1"],
        ("B", 2): params["nutrient_B_grain2"],
        ("B", 3): params["nutrient_B_grain3"],
        ("C", 1): params["nutrient_C_grain1"],
        ("C", 2): params["nutrient_C_grain2"],
        ("C", 3): params["nutrient_C_grain3"],
        ("D", 1): params["nutrient_D_grain1"],
        ("D", 2): params["nutrient_D_grain2"],
        ("D", 3): params["nutrient_D_grain3"],
    }
    requirement_data = {
        "A": params["req_A"],
        "B": params["req_B"],
        "C": params["req_C"],
        "D": params["req_D"],
    }

    model = pyo.ConcreteModel()
    model.G = pyo.Set(initialize=grains, ordered=True)
    model.N = pyo.Set(initialize=nutrients, ordered=True)

    model.cost = pyo.Param(model.G, initialize=cost_data, within=pyo.Reals)
    model.nutrient = pyo.Param(
        model.N, model.G, initialize=nutrient_data, within=pyo.Reals
    )
    model.requirement = pyo.Param(
        model.N, initialize=requirement_data, within=pyo.Reals
    )

    model.x = pyo.Var(model.G, domain=pyo.NonNegativeReals)

    def nutrient_requirement_rule(instance, nutrient_id):
        return sum(
            instance.nutrient[nutrient_id, grain_id] * instance.x[grain_id]
            for grain_id in instance.G
        ) >= instance.requirement[nutrient_id]

    model.nutrient_requirements = pyo.Constraint(
        model.N, rule=nutrient_requirement_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(model.cost[grain_id] * model.x[grain_id] for grain_id in model.G),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
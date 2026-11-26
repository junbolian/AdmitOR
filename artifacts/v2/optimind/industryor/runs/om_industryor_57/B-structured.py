# Assumption: the table's corrupted "?" symbols mean minimum A content
# for candies A and B, and maximum C content for candies A, B, and C.
# IR = {
#   "sets": {"raw_materials": ["A", "B", "C"], "candies": ["A", "B", "C"]},
#   "params": ["mat_cost_A", "mat_cost_B", "mat_cost_C", "limit_A", "limit_B", "limit_C", "proc_fee_A", "proc_fee_B", "proc_fee_C", "price_A", "price_B", "price_C", "content_A_in_A", "content_A_in_B", "content_C_in_A", "content_C_in_B", "content_C_in_C"],
#   "variables": {"production[candy]": "NonNegativeReals, kg", "allocation[raw_material,candy]": "NonNegativeReals, kg"},
#   "constraints": [
#     "For each candy j: sum_i allocation[i,j] == production[j].",
#     "For each raw material i: sum_j allocation[i,j] <= limit_i.",
#     "allocation[A,A] >= content_A_in_A * production[A].",
#     "allocation[A,B] >= content_A_in_B * production[B].",
#     "allocation[C,A] <= content_C_in_A * production[A].",
#     "allocation[C,B] <= content_C_in_B * production[B].",
#     "allocation[C,C] <= content_C_in_C * production[C]."
#   ],
#   "objective": "Maximize sum_j (price_j - proc_fee_j)*production[j] - sum_i sum_j mat_cost_i*allocation[i,j]."
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.raw_materials = pyo.Set(initialize=["A", "B", "C"], ordered=True)
    model.candies = pyo.Set(initialize=["A", "B", "C"], ordered=True)
    model.a_minimum_candies = pyo.Set(initialize=["A", "B"], ordered=True)

    model.material_cost = pyo.Param(
        model.raw_materials,
        initialize={
            "A": params["mat_cost_A"],
            "B": params["mat_cost_B"],
            "C": params["mat_cost_C"],
        },
    )
    model.material_limit = pyo.Param(
        model.raw_materials,
        initialize={
            "A": params["limit_A"],
            "B": params["limit_B"],
            "C": params["limit_C"],
        },
    )
    model.processing_fee = pyo.Param(
        model.candies,
        initialize={
            "A": params["proc_fee_A"],
            "B": params["proc_fee_B"],
            "C": params["proc_fee_C"],
        },
    )
    model.selling_price = pyo.Param(
        model.candies,
        initialize={
            "A": params["price_A"],
            "B": params["price_B"],
            "C": params["price_C"],
        },
    )
    model.minimum_a_content = pyo.Param(
        model.a_minimum_candies,
        initialize={
            "A": params["content_A_in_A"],
            "B": params["content_A_in_B"],
        },
    )
    model.maximum_c_content = pyo.Param(
        model.candies,
        initialize={
            "A": params["content_C_in_A"],
            "B": params["content_C_in_B"],
            "C": params["content_C_in_C"],
        },
    )

    model.production = pyo.Var(model.candies, domain=pyo.NonNegativeReals)
    model.allocation = pyo.Var(
        model.raw_materials,
        model.candies,
        domain=pyo.NonNegativeReals,
    )

    def mass_balance_rule(block, candy):
        return (
            sum(
                block.allocation[material, candy]
                for material in block.raw_materials
            )
            == block.production[candy]
        )

    model.mass_balance = pyo.Constraint(
        model.candies, rule=mass_balance_rule
    )

    def material_capacity_rule(block, material):
        return (
            sum(
                block.allocation[material, candy]
                for candy in block.candies
            )
            <= block.material_limit[material]
        )

    model.material_capacity = pyo.Constraint(
        model.raw_materials, rule=material_capacity_rule
    )

    def minimum_a_rule(block, candy):
        return (
            block.allocation["A", candy]
            >= block.minimum_a_content[candy] * block.production[candy]
        )

    model.minimum_a_requirement = pyo.Constraint(
        model.a_minimum_candies, rule=minimum_a_rule
    )

    def maximum_c_rule(block, candy):
        return (
            block.allocation["C", candy]
            <= block.maximum_c_content[candy] * block.production[candy]
        )

    model.maximum_c_requirement = pyo.Constraint(
        model.candies, rule=maximum_c_rule
    )

    model.profit_objective = pyo.Objective(
        expr=sum(
            (
                model.selling_price[candy]
                - model.processing_fee[candy]
            )
            * model.production[candy]
            for candy in model.candies
        )
        - sum(
            model.material_cost[material]
            * model.allocation[material, candy]
            for material in model.raw_materials
            for candy in model.candies
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Preserve unexpected runtime errors for the calling harness.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no feasible solution"}
        raise

    try:
        obj_val = float(pyo.value(model.profit_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    return {"objective": obj_val, "status": "optimal"}
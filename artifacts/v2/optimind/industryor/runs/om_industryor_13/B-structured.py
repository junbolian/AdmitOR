# IR: {
#   "sets": {
#     "P": ["chicken", "salmon", "tofu"],
#     "V": ["broccoli", "carrots", "spinach", "bell_pepper", "mushrooms"]
#   },
#   "params": [
#     "protein_chicken", "cost_chicken", "protein_salmon", "cost_salmon",
#     "protein_tofu", "cost_tofu", "protein_broccoli", "cost_broccoli",
#     "protein_carrots", "cost_carrots", "protein_spinach", "cost_spinach",
#     "protein_bell_pepper", "cost_bell_pepper",
#     "protein_mushrooms", "cost_mushrooms",
#     "budget", "max_weight", "min_vegetable_types"
#   ],
#   "units": {"food_quantity": "100g portions or packs", "grams_per_unit": 100},
#   "variables": {
#     "quantity[P]": "nonnegative continuous, measured in 100g portions",
#     "packs[V]": "nonnegative integer, number of 100g packs",
#     "selected[V]": "binary"
#   },
#   "constraints": [
#     "sum(cost[p]*quantity[p] for p in P) + sum(cost[v]*packs[v] for v in V) <= budget",
#     "100*(sum(quantity[p] for p in P) + sum(packs[v] for v in V)) <= max_weight",
#     "packs[v] >= selected[v] for each v in V",
#     "packs[v] <= (max_weight/100)*selected[v] for each v in V",
#     "sum(selected[v] for v in V) >= min_vegetable_types"
#   ],
#   "objective": "maximize sum(protein[p]*quantity[p] for p in P) + sum(protein[v]*packs[v] for v in V)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.protein_options = pyo.Set(
        initialize=["chicken", "salmon", "tofu"], ordered=True
    )
    model.vegetables = pyo.Set(
        initialize=[
            "broccoli",
            "carrots",
            "spinach",
            "bell_pepper",
            "mushrooms",
        ],
        ordered=True,
    )
    model.foods = model.protein_options | model.vegetables

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "salmon": params["protein_salmon"],
            "tofu": params["protein_tofu"],
            "broccoli": params["protein_broccoli"],
            "carrots": params["protein_carrots"],
            "spinach": params["protein_spinach"],
            "bell_pepper": params["protein_bell_pepper"],
            "mushrooms": params["protein_mushrooms"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "salmon": params["cost_salmon"],
            "tofu": params["cost_tofu"],
            "broccoli": params["cost_broccoli"],
            "carrots": params["cost_carrots"],
            "spinach": params["cost_spinach"],
            "bell_pepper": params["cost_bell_pepper"],
            "mushrooms": params["cost_mushrooms"],
        },
    )
    model.budget = pyo.Param(initialize=params["budget"])
    model.max_weight = pyo.Param(initialize=params["max_weight"])
    model.min_vegetable_types = pyo.Param(
        initialize=params["min_vegetable_types"]
    )

    model.quantity = pyo.Var(
        model.protein_options, domain=pyo.NonNegativeReals
    )
    model.packs = pyo.Var(
        model.vegetables, domain=pyo.NonNegativeIntegers
    )
    model.selected = pyo.Var(model.vegetables, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=(
            sum(
                model.cost[food] * model.quantity[food]
                for food in model.protein_options
            )
            + sum(
                model.cost[vegetable] * model.packs[vegetable]
                for vegetable in model.vegetables
            )
            <= model.budget
        )
    )

    # The factor 100 is the fixed grams-per-portion conversion.
    model.weight_limit = pyo.Constraint(
        expr=(
            100
            * (
                sum(
                    model.quantity[food]
                    for food in model.protein_options
                )
                + sum(
                    model.packs[vegetable]
                    for vegetable in model.vegetables
                )
            )
            <= model.max_weight
        )
    )

    def selected_pack_lower_rule(instance, vegetable):
        return instance.packs[vegetable] >= instance.selected[vegetable]

    model.selected_pack_lower = pyo.Constraint(
        model.vegetables, rule=selected_pack_lower_rule
    )

    def selected_pack_upper_rule(instance, vegetable):
        return (
            instance.packs[vegetable]
            <= (instance.max_weight / 100) * instance.selected[vegetable]
        )

    model.selected_pack_upper = pyo.Constraint(
        model.vegetables, rule=selected_pack_upper_rule
    )

    model.vegetable_variety = pyo.Constraint(
        expr=(
            sum(
                model.selected[vegetable]
                for vegetable in model.vegetables
            )
            >= model.min_vegetable_types
        )
    )

    model.total_protein = pyo.Objective(
        expr=(
            sum(
                model.protein[food] * model.quantity[food]
                for food in model.protein_options
            )
            + sum(
                model.protein[vegetable] * model.packs[vegetable]
                for vegetable in model.vegetables
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions propagate to the caller.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_protein))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {
#   "sets": {"single_assets": ["painting", "bust", "vase", "porsche", "sofa", "sculpture", "sailboat", "harley", "cavour_furniture"]},
#   "params": ["painting_value", "bust_value", "vase_value", "porsche_value", "diamond_value", "diamond_count", "sofa_value", "dog_value", "dog_count", "sculpture_value", "sailboat_value", "harley_value", "cavour_furniture_value"],
#   "variables": {"assigned[a]": "binary; asset a goes to son 1", "diamonds_assigned": "integer in [0, diamond_count]; diamonds going to son 1", "dogs_assigned": "binary; all dogs go to son 1", "difference": "nonnegative continuous"},
#   "expressions": {"total_value": "sum(single_asset_values) + diamond_value*diamond_count + dog_value*dog_count", "first_share": "sum(asset_value[a]*assigned[a]) + diamond_value*diamonds_assigned + dog_value*dog_count*dogs_assigned", "second_share": "total_value - first_share"},
#   "constraints": ["difference >= first_share - second_share", "difference >= second_share - first_share"],
#   "objective": "minimize difference"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    single_assets = (
        "painting",
        "bust",
        "vase",
        "porsche",
        "sofa",
        "sculpture",
        "sailboat",
        "harley",
        "cavour_furniture",
    )

    asset_values = {
        "painting": params["painting_value"],
        "bust": params["bust_value"],
        "vase": params["vase_value"],
        "porsche": params["porsche_value"],
        "sofa": params["sofa_value"],
        "sculpture": params["sculpture_value"],
        "sailboat": params["sailboat_value"],
        "harley": params["harley_value"],
        "cavour_furniture": params["cavour_furniture_value"],
    }
    diamond_value = params["diamond_value"]
    diamond_count = params["diamond_count"]
    dog_value = params["dog_value"]
    dog_count = params["dog_count"]

    model = pyo.ConcreteModel()
    model.single_assets = pyo.Set(initialize=single_assets, ordered=True)

    model.asset_values = pyo.Param(
        model.single_assets, initialize=asset_values
    )
    model.diamond_value = pyo.Param(initialize=diamond_value)
    model.diamond_count = pyo.Param(
        initialize=diamond_count, within=pyo.NonNegativeIntegers
    )
    model.dog_value = pyo.Param(initialize=dog_value)
    model.dog_count = pyo.Param(
        initialize=dog_count, within=pyo.NonNegativeIntegers
    )

    model.assigned = pyo.Var(model.single_assets, domain=pyo.Binary)
    model.diamonds_assigned = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, diamond_count),
    )
    model.dogs_assigned = pyo.Var(domain=pyo.Binary)
    model.difference = pyo.Var(domain=pyo.NonNegativeReals)

    # Each unassigned asset goes to son 2; dogs form one indivisible bundle.
    model.total_value = pyo.Expression(
        expr=sum(model.asset_values[asset] for asset in model.single_assets)
        + model.diamond_value * model.diamond_count
        + model.dog_value * model.dog_count
    )
    model.first_share = pyo.Expression(
        expr=sum(
            model.asset_values[asset] * model.assigned[asset]
            for asset in model.single_assets
        )
        + model.diamond_value * model.diamonds_assigned
        + model.dog_value * model.dog_count * model.dogs_assigned
    )
    model.second_share = pyo.Expression(
        expr=model.total_value - model.first_share
    )

    model.first_excess = pyo.Constraint(
        expr=model.difference >= model.first_share - model.second_share
    )
    model.second_excess = pyo.Constraint(
        expr=model.difference >= model.second_share - model.first_share
    )
    model.minimum_difference = pyo.Objective(
        expr=model.difference, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.minimum_difference))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
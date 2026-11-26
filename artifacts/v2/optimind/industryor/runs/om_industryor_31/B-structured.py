# IR: {"sets":{"assets":["painting","bust","vase","porsche","diamond_1","diamond_2","diamond_3","sofa","dog_pair","sculpture","boat","motorcycle","cavour_furniture"],"sons":[1,2]},"params":["painting_value","bust_value","vase_value","porsche_value","diamond_value","sofa_value","dog_value","sculpture_value","boat_value","motorcycle_value","cavour_furniture_value"],"derived":{"value[a]":"corresponding params entry; each diamond uses diamond_value; dog_pair uses 2*dog_value","total_value":"sum(value[a] for a in assets)"},"variables":{"assigned[a]":"binary; 1 assigns asset a to son 1, 0 assigns it to son 2","difference":"nonnegative continuous"},"constraints":["difference >= 2*sum(value[a]*assigned[a] for a in assets)-total_value","difference >= total_value-2*sum(value[a]*assigned[a] for a in assets)"],"objective":"minimize difference"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    asset_values = {
        "painting": params["painting_value"],
        "bust": params["bust_value"],
        "vase": params["vase_value"],
        "porsche": params["porsche_value"],
        "diamond_1": params["diamond_value"],
        "diamond_2": params["diamond_value"],
        "diamond_3": params["diamond_value"],
        "sofa": params["sofa_value"],
        "dog_pair": 2 * params["dog_value"],
        "sculpture": params["sculpture_value"],
        "boat": params["boat_value"],
        "motorcycle": params["motorcycle_value"],
        "cavour_furniture": params["cavour_furniture_value"],
    }

    model = pyo.ConcreteModel()
    model.assets = pyo.Set(initialize=list(asset_values), ordered=True)
    model.sons = pyo.Set(initialize=[1, 2], ordered=True)
    model.asset_value = pyo.Param(
        model.assets,
        initialize=asset_values,
        within=pyo.Reals,
    )

    # Each asset goes to exactly one son through its binary assignment.
    # The two dogs form one indivisible asset, so they stay together.
    model.assigned = pyo.Var(model.assets, domain=pyo.Binary)
    model.difference = pyo.Var(domain=pyo.NonNegativeReals)

    model.total_value = pyo.Expression(
        expr=sum(model.asset_value[asset] for asset in model.assets)
    )
    model.first_son_value = pyo.Expression(
        expr=sum(
            model.asset_value[asset] * model.assigned[asset]
            for asset in model.assets
        )
    )

    model.positive_difference_bound = pyo.Constraint(
        expr=model.difference
        >= 2 * model.first_son_value - model.total_value
    )
    model.negative_difference_bound = pyo.Constraint(
        expr=model.difference
        >= model.total_value - 2 * model.first_son_value
    )

    model.objective = pyo.Objective(
        expr=model.difference,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Still use objective retrieval as the sole success test.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
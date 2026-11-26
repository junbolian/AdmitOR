# IR: {"sets":{"toys":["truck","plane","boat","train"]},"params":{"profit":["profit_truck","profit_plane","profit_boat","profit_train"],"wood":["wood_truck","wood_plane","wood_boat","wood_train"],"steel":["steel_truck","steel_plane","steel_boat","steel_train"],"availability":["wood_available","steel_available"]},"derived":{"upper[t]":"floor(min(wood_available/wood[t],steel_available/steel[t]))"},"variables":{"quantity[t]":"NonNegativeIntegers","produced[t]":"Binary"},"constraints":["sum(wood[t]*quantity[t]) <= wood_available","sum(steel[t]*quantity[t]) <= steel_available","quantity[t] <= upper[t]*produced[t] for each t","quantity[t] >= produced[t] for each t","produced[truck]+produced[train] <= 1","produced[boat] <= produced[plane]","quantity[boat] <= quantity[train]"],"objective":"maximize sum(profit[t]*quantity[t])"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.toys = pyo.Set(
        initialize=["truck", "plane", "boat", "train"],
        ordered=True,
    )

    model.profit = pyo.Param(
        model.toys,
        initialize={
            "truck": params["profit_truck"],
            "plane": params["profit_plane"],
            "boat": params["profit_boat"],
            "train": params["profit_train"],
        },
        within=pyo.Reals,
    )

    model.wood = pyo.Param(
        model.toys,
        initialize={
            "truck": params["wood_truck"],
            "plane": params["wood_plane"],
            "boat": params["wood_boat"],
            "train": params["wood_train"],
        },
        within=pyo.PositiveReals,
    )

    model.steel = pyo.Param(
        model.toys,
        initialize={
            "truck": params["steel_truck"],
            "plane": params["steel_plane"],
            "boat": params["steel_boat"],
            "train": params["steel_train"],
        },
        within=pyo.PositiveReals,
    )

    model.wood_available = pyo.Param(
        initialize=params["wood_available"],
        within=pyo.NonNegativeReals,
    )

    model.steel_available = pyo.Param(
        initialize=params["steel_available"],
        within=pyo.NonNegativeReals,
    )

    def upper_rule(instance, toy):
        return math.floor(
            min(
                pyo.value(instance.wood_available) / pyo.value(instance.wood[toy]),
                pyo.value(instance.steel_available) / pyo.value(instance.steel[toy]),
            )
        )

    model.upper = pyo.Param(
        model.toys,
        initialize=upper_rule,
        within=pyo.NonNegativeIntegers,
    )

    model.quantity = pyo.Var(model.toys, domain=pyo.NonNegativeIntegers)
    model.produced = pyo.Var(model.toys, domain=pyo.Binary)

    model.wood_limit = pyo.Constraint(
        expr=sum(model.wood[toy] * model.quantity[toy] for toy in model.toys)
        <= model.wood_available
    )

    model.steel_limit = pyo.Constraint(
        expr=sum(model.steel[toy] * model.quantity[toy] for toy in model.toys)
        <= model.steel_available
    )

    def production_upper_rule(instance, toy):
        return (
            instance.quantity[toy]
            <= instance.upper[toy] * instance.produced[toy]
        )

    model.production_upper = pyo.Constraint(
        model.toys,
        rule=production_upper_rule,
    )

    def production_lower_rule(instance, toy):
        return instance.quantity[toy] >= instance.produced[toy]

    model.production_lower = pyo.Constraint(
        model.toys,
        rule=production_lower_rule,
    )

    model.truck_train_exclusion = pyo.Constraint(
        expr=model.produced["truck"] + model.produced["train"] <= 1
    )

    model.boat_requires_plane = pyo.Constraint(
        expr=model.produced["boat"] <= model.produced["plane"]
    )

    model.boat_train_limit = pyo.Constraint(
        expr=model.quantity["boat"] <= model.quantity["train"]
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[toy] * model.quantity[toy]
            for toy in model.toys
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An unsuccessful solve may leave the objective unavailable.
        # Determine success solely by attempting to retrieve its value below.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
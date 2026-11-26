# IR: {"sets":{"toys":["truck","airplane","boat","train"]},"params":["profit_truck","profit_airplane","profit_boat","profit_train","wood_capacity","wood_truck","wood_airplane","wood_boat","wood_train","steel_capacity","steel_truck","steel_airplane","steel_boat","steel_train"],"derived":{"upper_bound[t]":"floor(min(wood_capacity/wood[t], steel_capacity/steel[t]))"},"variables":{"quantity[t]":"nonnegative integer","manufacture[t]":"binary"},"constraints":["sum(wood[t]*quantity[t] for t in toys) <= wood_capacity","sum(steel[t]*quantity[t] for t in toys) <= steel_capacity","quantity[t] <= upper_bound[t]*manufacture[t] for t in toys","quantity[t] >= manufacture[t] for t in toys","manufacture[truck] + manufacture[train] <= 1","manufacture[boat] <= manufacture[airplane]","quantity[boat] <= quantity[train]"],"objective":"maximize sum(profit[t]*quantity[t] for t in toys)"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    toys = ("truck", "airplane", "boat", "train")

    profit = {
        "truck": params["profit_truck"],
        "airplane": params["profit_airplane"],
        "boat": params["profit_boat"],
        "train": params["profit_train"],
    }
    wood_capacity = params["wood_capacity"]
    wood = {
        "truck": params["wood_truck"],
        "airplane": params["wood_airplane"],
        "boat": params["wood_boat"],
        "train": params["wood_train"],
    }
    steel_capacity = params["steel_capacity"]
    steel = {
        "truck": params["steel_truck"],
        "airplane": params["steel_airplane"],
        "boat": params["steel_boat"],
        "train": params["steel_train"],
    }

    upper_bound = {
        toy: math.floor(
            min(
                wood_capacity / wood[toy],
                steel_capacity / steel[toy],
            )
        )
        for toy in toys
    }

    model = pyo.ConcreteModel()
    model.toys = pyo.Set(initialize=toys, ordered=True)

    model.quantity = pyo.Var(model.toys, domain=pyo.NonNegativeIntegers)
    model.manufacture = pyo.Var(model.toys, domain=pyo.Binary)

    model.wood_limit = pyo.Constraint(
        expr=sum(wood[toy] * model.quantity[toy] for toy in toys)
        <= wood_capacity
    )
    model.steel_limit = pyo.Constraint(
        expr=sum(steel[toy] * model.quantity[toy] for toy in toys)
        <= steel_capacity
    )

    def production_upper_rule(current_model, toy):
        return (
            current_model.quantity[toy]
            <= upper_bound[toy] * current_model.manufacture[toy]
        )

    def production_lower_rule(current_model, toy):
        return current_model.quantity[toy] >= current_model.manufacture[toy]

    model.production_upper = pyo.Constraint(
        model.toys, rule=production_upper_rule
    )
    model.production_lower = pyo.Constraint(
        model.toys, rule=production_lower_rule
    )

    model.truck_train_exclusion = pyo.Constraint(
        expr=model.manufacture["truck"] + model.manufacture["train"] <= 1
    )
    model.boat_requires_airplane = pyo.Constraint(
        expr=model.manufacture["boat"] <= model.manufacture["airplane"]
    )
    model.boat_train_limit = pyo.Constraint(
        expr=model.quantity["boat"] <= model.quantity["train"]
    )

    model.total_profit = pyo.Objective(
        expr=sum(profit[toy] * model.quantity[toy] for toy in toys),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
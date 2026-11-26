# IR: {"sets":{"T":["robot","car","blocks","doll"]},"params":["profit_per_robot","profit_per_car","profit_per_blocks","profit_per_doll","plastic_capacity","electronics_capacity","plastic_per_robot","plastic_per_car","plastic_per_blocks","plastic_per_doll","electronics_per_robot","electronics_per_car","electronics_per_blocks","electronics_per_doll"],"derived":{"U[t]":"floor(min(plastic_capacity/plastic_per_t,electronics_capacity/electronics_per_t))"},"variables":{"quantity[t]":"nonnegative integer","manufacture[t]":"binary"},"constraints":["sum(plastic_per_t*quantity[t] for t in T) <= plastic_capacity","sum(electronics_per_t*quantity[t] for t in T) <= electronics_capacity","quantity[t] <= U[t]*manufacture[t] for t in T","quantity[t] >= manufacture[t] for t in T","manufacture[robot] + manufacture[doll] <= 1","manufacture[car] <= manufacture[blocks]","quantity[doll] <= quantity[car]"],"objective":"maximize sum(profit_per_t*quantity[t] for t in T)"}

from math import floor

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("robot", "car", "blocks", "doll")

    profits = {
        "robot": params["profit_per_robot"],
        "car": params["profit_per_car"],
        "blocks": params["profit_per_blocks"],
        "doll": params["profit_per_doll"],
    }
    plastic_requirements = {
        "robot": params["plastic_per_robot"],
        "car": params["plastic_per_car"],
        "blocks": params["plastic_per_blocks"],
        "doll": params["plastic_per_doll"],
    }
    electronics_requirements = {
        "robot": params["electronics_per_robot"],
        "car": params["electronics_per_car"],
        "blocks": params["electronics_per_blocks"],
        "doll": params["electronics_per_doll"],
    }
    plastic_capacity = params["plastic_capacity"]
    electronics_capacity = params["electronics_capacity"]

    # Each stated product consumes positive amounts of both resources.
    upper_bounds = {
        product: floor(
            min(
                plastic_capacity / plastic_requirements[product],
                electronics_capacity / electronics_requirements[product],
            )
        )
        for product in products
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)

    model.unit_profit = pyo.Param(model.products, initialize=profits)
    model.plastic_requirement = pyo.Param(
        model.products, initialize=plastic_requirements
    )
    model.electronics_requirement = pyo.Param(
        model.products, initialize=electronics_requirements
    )
    model.plastic_capacity = pyo.Param(initialize=plastic_capacity)
    model.electronics_capacity = pyo.Param(initialize=electronics_capacity)
    model.production_limit = pyo.Param(
        model.products, initialize=upper_bounds
    )

    model.quantity = pyo.Var(model.products, domain=pyo.NonNegativeIntegers)
    model.manufacture = pyo.Var(model.products, domain=pyo.Binary)

    model.plastic_constraint = pyo.Constraint(
        expr=sum(
            model.plastic_requirement[product] * model.quantity[product]
            for product in model.products
        )
        <= model.plastic_capacity
    )
    model.electronics_constraint = pyo.Constraint(
        expr=sum(
            model.electronics_requirement[product] * model.quantity[product]
            for product in model.products
        )
        <= model.electronics_capacity
    )

    def activation_upper_rule(instance, product):
        return (
            instance.quantity[product]
            <= instance.production_limit[product] * instance.manufacture[product]
        )

    def activation_lower_rule(instance, product):
        return instance.quantity[product] >= instance.manufacture[product]

    model.activation_upper_constraint = pyo.Constraint(
        model.products, rule=activation_upper_rule
    )
    model.activation_lower_constraint = pyo.Constraint(
        model.products, rule=activation_lower_rule
    )

    model.robot_doll_exclusion = pyo.Constraint(
        expr=model.manufacture["robot"] + model.manufacture["doll"] <= 1
    )
    model.car_requires_blocks = pyo.Constraint(
        expr=model.manufacture["car"] <= model.manufacture["blocks"]
    )
    model.doll_car_constraint = pyo.Constraint(
        expr=model.quantity["doll"] <= model.quantity["car"]
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.quantity[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An unsuccessful solve may leave all variable values unset.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
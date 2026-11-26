# IR: {"sets":{"T":["robot","model_car","building_blocks","doll"]},"params":{"profit":"T-indexed","plastic_avail":"scalar","electronics_avail":"scalar","plastic_req":"T-indexed, positive","electronics_req":"T-indexed, positive"},"derived":{"U[t]":"max(0,min(floor(plastic_avail/plastic_req[t]),floor(electronics_avail/electronics_req[t])))"},"variables":{"quantity[t]":"nonnegative integer","produced[t]":"binary"},"constraints":["sum(plastic_req[t]*quantity[t] for t in T)<=plastic_avail","sum(electronics_req[t]*quantity[t] for t in T)<=electronics_avail","quantity[t]<=U[t]*produced[t] for t in T","quantity[t]>=produced[t] for t in T","produced[robot]+produced[doll]<=1","produced[model_car]<=produced[building_blocks]","quantity[doll]<=quantity[model_car]"],"objective":"maximize sum(profit[t]*quantity[t] for t in T)"}

from collections.abc import Mapping
from math import floor

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept indexed parameters as mappings or sequences in toy order."""
    toys = ("robot", "model_car", "building_blocks", "doll")

    def indexed_values(values):
        if isinstance(values, Mapping):
            return {
                toy: values[toy] if toy in values else values[toy.replace("_", " ")]
                for toy in toys
            }
        return {toy: values[position] for position, toy in enumerate(toys)}

    profit = indexed_values(params["profit"])
    plastic_avail = params["plastic_avail"]
    electronics_avail = params["electronics_avail"]
    plastic_req = indexed_values(params["plastic_req"])
    electronics_req = indexed_values(params["electronics_req"])

    upper_bounds = {
        toy: max(
            0,
            min(
                floor(plastic_avail / plastic_req[toy]),
                floor(electronics_avail / electronics_req[toy]),
            ),
        )
        for toy in toys
    }

    model = pyo.ConcreteModel()
    model.toys = pyo.Set(initialize=toys, ordered=True)

    model.unit_profit = pyo.Param(model.toys, initialize=profit)
    model.plastic_capacity = pyo.Param(initialize=plastic_avail)
    model.electronics_capacity = pyo.Param(initialize=electronics_avail)
    model.plastic_per_unit = pyo.Param(model.toys, initialize=plastic_req)
    model.electronics_per_unit = pyo.Param(model.toys, initialize=electronics_req)
    model.production_upper_bound = pyo.Param(
        model.toys, initialize=upper_bounds, within=pyo.NonNegativeIntegers
    )

    model.quantity = pyo.Var(model.toys, domain=pyo.NonNegativeIntegers)
    model.produced = pyo.Var(model.toys, domain=pyo.Binary)

    model.plastic_limit = pyo.Constraint(
        expr=sum(
            model.plastic_per_unit[toy] * model.quantity[toy]
            for toy in model.toys
        )
        <= model.plastic_capacity
    )
    model.electronics_limit = pyo.Constraint(
        expr=sum(
            model.electronics_per_unit[toy] * model.quantity[toy]
            for toy in model.toys
        )
        <= model.electronics_capacity
    )

    def production_upper_rule(problem, toy):
        return (
            problem.quantity[toy]
            <= problem.production_upper_bound[toy] * problem.produced[toy]
        )

    def production_lower_rule(problem, toy):
        return problem.quantity[toy] >= problem.produced[toy]

    model.production_upper_link = pyo.Constraint(
        model.toys, rule=production_upper_rule
    )
    model.production_lower_link = pyo.Constraint(
        model.toys, rule=production_lower_rule
    )

    model.robot_doll_exclusion = pyo.Constraint(
        expr=model.produced["robot"] + model.produced["doll"] <= 1
    )
    model.car_requires_blocks = pyo.Constraint(
        expr=model.produced["model_car"] <= model.produced["building_blocks"]
    )
    model.dolls_not_above_cars = pyo.Constraint(
        expr=model.quantity["doll"] <= model.quantity["model_car"]
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[toy] * model.quantity[toy]
            for toy in model.toys
        ),
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
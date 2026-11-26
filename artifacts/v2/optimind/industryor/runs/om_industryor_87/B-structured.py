# IR: {"sets":{"products":["A","B"]},"params":["profit_A","profit_B","hours_available","hours_per_A","hours_per_B","demand_ratio_B_to_A","space_per_A","space_per_B","storage_capacity"],"variables":{"quantity[products]":"nonnegative integer"},"constraints":["hours_per_A*quantity[A]+hours_per_B*quantity[B]<=hours_available","quantity[B]>=demand_ratio_B_to_A*quantity[A]","space_per_A*quantity[A]+space_per_B*quantity[B]<=storage_capacity"],"objective":"maximize profit_A*quantity[A]+profit_B*quantity[B]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["A", "B"], ordered=True)

    model.profit_A = pyo.Param(initialize=params["profit_A"])
    model.profit_B = pyo.Param(initialize=params["profit_B"])
    model.hours_available = pyo.Param(initialize=params["hours_available"])
    model.hours_per_A = pyo.Param(initialize=params["hours_per_A"])
    model.hours_per_B = pyo.Param(initialize=params["hours_per_B"])
    model.demand_ratio_B_to_A = pyo.Param(
        initialize=params["demand_ratio_B_to_A"]
    )
    model.space_per_A = pyo.Param(initialize=params["space_per_A"])
    model.space_per_B = pyo.Param(initialize=params["space_per_B"])
    model.storage_capacity = pyo.Param(initialize=params["storage_capacity"])

    model.quantity = pyo.Var(model.products, domain=pyo.NonNegativeIntegers)

    model.production_hours_limit = pyo.Constraint(
        expr=(
            model.hours_per_A * model.quantity["A"]
            + model.hours_per_B * model.quantity["B"]
            <= model.hours_available
        )
    )

    model.minimum_demand_ratio = pyo.Constraint(
        expr=(
            model.quantity["B"]
            >= model.demand_ratio_B_to_A * model.quantity["A"]
        )
    )

    model.storage_limit = pyo.Constraint(
        expr=(
            model.space_per_A * model.quantity["A"]
            + model.space_per_B * model.quantity["B"]
            <= model.storage_capacity
        )
    )

    model.total_profit = pyo.Objective(
        expr=(
            model.profit_A * model.quantity["A"]
            + model.profit_B * model.quantity["B"]
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
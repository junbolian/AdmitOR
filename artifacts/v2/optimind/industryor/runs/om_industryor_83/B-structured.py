# IR: {"sets":{"products":["X","Y"]},"params":["machine_minutes_X","craftsman_minutes_X","machine_minutes_Y","craftsman_minutes_Y","machine_hours_capacity","craftsman_hours_capacity","machine_cost_per_hour","craftsman_cost_per_hour","revenue_X","revenue_Y","contract_min_X"],"variables":{"units[products]":"nonnegative integer"},"constraints":["machine_minutes_X*units[X]+machine_minutes_Y*units[Y] <= 60*machine_hours_capacity","craftsman_minutes_X*units[X]+craftsman_minutes_Y*units[Y] <= 60*craftsman_hours_capacity","units[X] >= contract_min_X"],"objective":{"sense":"maximize","expression":"revenue_X*units[X]+revenue_Y*units[Y]-(machine_cost_per_hour/60)*(machine_minutes_X*units[X]+machine_minutes_Y*units[Y])-(craftsman_cost_per_hour/60)*(craftsman_minutes_X*units[X]+craftsman_minutes_Y*units[Y])"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["X", "Y"], ordered=True)

    model.machine_minutes_X = pyo.Param(
        initialize=params["machine_minutes_X"]
    )
    model.craftsman_minutes_X = pyo.Param(
        initialize=params["craftsman_minutes_X"]
    )
    model.machine_minutes_Y = pyo.Param(
        initialize=params["machine_minutes_Y"]
    )
    model.craftsman_minutes_Y = pyo.Param(
        initialize=params["craftsman_minutes_Y"]
    )
    model.machine_hours_capacity = pyo.Param(
        initialize=params["machine_hours_capacity"]
    )
    model.craftsman_hours_capacity = pyo.Param(
        initialize=params["craftsman_hours_capacity"]
    )
    model.machine_cost_per_hour = pyo.Param(
        initialize=params["machine_cost_per_hour"]
    )
    model.craftsman_cost_per_hour = pyo.Param(
        initialize=params["craftsman_cost_per_hour"]
    )
    model.revenue_X = pyo.Param(initialize=params["revenue_X"])
    model.revenue_Y = pyo.Param(initialize=params["revenue_Y"])
    model.contract_min_X = pyo.Param(initialize=params["contract_min_X"])

    model.units = pyo.Var(model.products, domain=pyo.NonNegativeIntegers)

    machine_minutes_used = (
        model.machine_minutes_X * model.units["X"]
        + model.machine_minutes_Y * model.units["Y"]
    )
    craftsman_minutes_used = (
        model.craftsman_minutes_X * model.units["X"]
        + model.craftsman_minutes_Y * model.units["Y"]
    )

    # Unit conversion: 60 minutes per hour.
    model.machine_capacity_constraint = pyo.Constraint(
        expr=machine_minutes_used <= 60 * model.machine_hours_capacity
    )
    model.craftsman_capacity_constraint = pyo.Constraint(
        expr=craftsman_minutes_used <= 60 * model.craftsman_hours_capacity
    )
    model.contract_constraint = pyo.Constraint(
        expr=model.units["X"] >= model.contract_min_X
    )

    model.profit = pyo.Objective(
        expr=(
            model.revenue_X * model.units["X"]
            + model.revenue_Y * model.units["Y"]
            - model.machine_cost_per_hour * machine_minutes_used / 60
            - model.craftsman_cost_per_hour * craftsman_minutes_used / 60
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors must propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Success is determined solely by objective-value retrieval.
    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
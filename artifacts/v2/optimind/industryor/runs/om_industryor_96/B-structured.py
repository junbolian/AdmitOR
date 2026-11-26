# IR: {"sets":{},"params":["profit_A","profit_B","steel_A","steel_B","aluminum_A","aluminum_B","labor_A","labor_B","steel_capacity","aluminum_capacity","labor_capacity","overtime_pay"],"variables":{"quantity_A":"nonnegative integer","quantity_B":"nonnegative integer","overtime":"nonnegative real"},"constraints":["steel_A*quantity_A + steel_B*quantity_B <= steel_capacity","aluminum_A*quantity_A + aluminum_B*quantity_B <= aluminum_capacity","labor_A*quantity_A + labor_B*quantity_B <= labor_capacity + overtime"],"objective":{"sense":"maximize","expression":"profit_A*quantity_A + profit_B*quantity_B - overtime_pay*overtime"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.profit_A = pyo.Param(initialize=params["profit_A"])
    model.profit_B = pyo.Param(initialize=params["profit_B"])
    model.steel_A = pyo.Param(initialize=params["steel_A"])
    model.steel_B = pyo.Param(initialize=params["steel_B"])
    model.aluminum_A = pyo.Param(initialize=params["aluminum_A"])
    model.aluminum_B = pyo.Param(initialize=params["aluminum_B"])
    model.labor_A = pyo.Param(initialize=params["labor_A"])
    model.labor_B = pyo.Param(initialize=params["labor_B"])
    model.steel_capacity = pyo.Param(initialize=params["steel_capacity"])
    model.aluminum_capacity = pyo.Param(
        initialize=params["aluminum_capacity"]
    )
    model.labor_capacity = pyo.Param(initialize=params["labor_capacity"])
    model.overtime_pay = pyo.Param(initialize=params["overtime_pay"])

    model.quantity_A = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.quantity_B = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.overtime = pyo.Var(domain=pyo.NonNegativeReals)

    model.steel_limit = pyo.Constraint(
        expr=model.steel_A * model.quantity_A
        + model.steel_B * model.quantity_B
        <= model.steel_capacity
    )

    model.aluminum_limit = pyo.Constraint(
        expr=model.aluminum_A * model.quantity_A
        + model.aluminum_B * model.quantity_B
        <= model.aluminum_capacity
    )

    model.labor_limit = pyo.Constraint(
        expr=model.labor_A * model.quantity_A
        + model.labor_B * model.quantity_B
        <= model.labor_capacity + model.overtime
    )

    model.total_profit = pyo.Objective(
        expr=model.profit_A * model.quantity_A
        + model.profit_B * model.quantity_B
        - model.overtime_pay * model.overtime,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    steel_A = params["steel_A"]
    steel_B = params["steel_B"]
    aluminum_A = params["aluminum_A"]
    aluminum_B = params["aluminum_B"]
    labor_A = params["labor_A"]
    labor_B = params["labor_B"]
    steel_capacity = params["steel_capacity"]
    aluminum_capacity = params["aluminum_capacity"]
    labor_capacity = params["labor_capacity"]
    overtime_pay = params["overtime_pay"]

    model = pyo.ConcreteModel()

    model.A = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.B = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.overtime = pyo.Var(domain=pyo.NonNegativeReals)

    model.steel_con = pyo.Constraint(
        expr=steel_A * model.A + steel_B * model.B <= steel_capacity
    )
    model.aluminum_con = pyo.Constraint(
        expr=aluminum_A * model.A + aluminum_B * model.B <= aluminum_capacity
    )
    model.labor_con = pyo.Constraint(
        expr=labor_A * model.A + labor_B * model.B <= labor_capacity + model.overtime
    )

    model.obj = pyo.Objective(
        expr=profit_A * model.A + profit_B * model.B - overtime_pay * model.overtime,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
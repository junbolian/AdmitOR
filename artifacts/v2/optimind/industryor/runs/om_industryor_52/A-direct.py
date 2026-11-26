import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hours_A = params["equipment_hours_per_unit_A"]
    hours_B = params["equipment_hours_per_unit_B"]
    hours_C = params["equipment_hours_per_unit_C"]
    cap_A = params["capacity_A"]
    cap_B = params["capacity_B"]
    cap_C = params["capacity_C"]
    profit = params["unit_profit"]

    products = [0, 1, 2]

    model = pyo.ConcreteModel()

    model.qty = pyo.Var(products, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.qty[i] for i in products),
        sense=pyo.maximize,
    )

    model.capA = pyo.Constraint(
        expr=sum(hours_A[i] * model.qty[i] for i in products) <= cap_A
    )
    model.capB = pyo.Constraint(
        expr=sum(hours_B[i] * model.qty[i] for i in products) <= cap_B
    )
    model.capC = pyo.Constraint(
        expr=sum(hours_C[i] * model.qty[i] for i in products) <= cap_C
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}
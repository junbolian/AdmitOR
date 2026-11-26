import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_capital = params["initial_capital"]
    rate_project1 = params["rate_project1"]
    multiplier_project2 = params["multiplier_project2"]
    cap_project2 = params["cap_project2"]
    multiplier_project3 = params["multiplier_project3"]
    cap_project3 = params["cap_project3"]
    multiplier_project4 = params["multiplier_project4"]
    cap_project4 = params["cap_project4"]

    years = [1, 2, 3]

    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(years, domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x3 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x4 = pyo.Var(domain=pyo.NonNegativeReals)

    model.cap2 = pyo.Constraint(expr=model.x2 <= cap_project2)
    model.cap3 = pyo.Constraint(expr=model.x3 <= cap_project3)
    model.cap4 = pyo.Constraint(expr=model.x4 <= cap_project4)

    model.bal1 = pyo.Constraint(
        expr=model.x1[1] + model.x2 <= initial_capital
    )
    model.bal2 = pyo.Constraint(
        expr=model.x1[2] + model.x3
        <= (1.0 + rate_project1) * model.x1[1] + multiplier_project2 * model.x2
    )
    model.bal3 = pyo.Constraint(
        expr=model.x1[3] + model.x4
        <= (1.0 + rate_project1) * model.x1[2] + multiplier_project3 * model.x3
    )

    model.final_wealth = pyo.Expression(
        expr=(1.0 + rate_project1) * model.x1[3] + multiplier_project4 * model.x4
    )

    model.obj = pyo.Objective(expr=model.final_wealth, sense=pyo.maximize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
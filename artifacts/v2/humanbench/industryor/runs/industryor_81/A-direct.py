import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_capital = params["initial_capital"]
    r1 = params["annual_reinvest_profit_rate"]
    r2 = params["project2_total_interest_rate"]
    cap2 = params["project2_investment_cap"]
    r3 = params["project3_total_interest_rate"]
    cap3 = params["project3_investment_cap"]
    r4 = params["project4_profit_rate"]
    cap4 = params["project4_investment_cap"]

    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)  # project 1 invested each year
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)  # project 2
    model.x3 = pyo.Var(domain=pyo.NonNegativeReals)  # project 3
    model.x4 = pyo.Var(domain=pyo.NonNegativeReals)  # project 4

    model.cap2 = pyo.Constraint(expr=model.x2 <= cap2)
    model.cap3 = pyo.Constraint(expr=model.x3 <= cap3)
    model.cap4 = pyo.Constraint(expr=model.x4 <= cap4)

    # Beginning of year 1: invest in project 1 and project 2
    model.budget1 = pyo.Constraint(
        expr=model.x1 + model.x2 <= initial_capital
    )

    # Beginning of year 2: available from project 1 (principal + profit) plus
    # recovered project 2 (principal + interest), invest in project 1 and 3
    model.budget2 = pyo.Constraint(
        expr=model.x1 + model.x3 <= (1 + r1) * model.x1 + (1 + r2) * model.x2
    )

    # Beginning of year 3: available from project 1 profits, project 3,
    # invest in project 1 and project 4
    model.budget3 = pyo.Constraint(
        expr=model.x1 + model.x4 <= (1 + r1) * model.x1 + (1 + r3) * model.x3
    )

    # Objective: total interest / final wealth at end of year 3
    model.obj = pyo.Objective(
        expr=(1 + r1) * model.x1 + (1 + r4) * model.x4,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
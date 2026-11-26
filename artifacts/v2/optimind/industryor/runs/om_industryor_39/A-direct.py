import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fund = params["fund"]
    r1 = params["project1_rate"]
    r2 = params["project2_return"]
    c2 = params["project2_cap"]
    r3 = params["project3_return"]
    c3 = params["project3_cap"]
    r4 = params["project4_return"]
    c4 = params["project4_cap"]

    years = [1, 2, 3]
    model = pyo.ConcreteModel()

    # Decision variables (amounts invested / cash kept)
    model.x1 = pyo.Var(years, domain=pyo.NonNegativeReals)  # project 1 each year
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)          # project 2 (year 1)
    model.x3 = pyo.Var(domain=pyo.NonNegativeReals)          # project 3 (year 2)
    model.x4 = pyo.Var(domain=pyo.NonNegativeReals)          # project 4 (year 3)
    model.s = pyo.Var(years, domain=pyo.NonNegativeReals)    # idle cash carried

    # Capacity limits
    model.cap2 = pyo.Constraint(expr=model.x2 <= c2)
    model.cap3 = pyo.Constraint(expr=model.x3 <= c3)
    model.cap4 = pyo.Constraint(expr=model.x4 <= c4)

    # Start of year 1: initial fund allocated
    model.y1 = pyo.Constraint(
        expr=model.x1[1] + model.x2 + model.s[1] == fund
    )

    # Start of year 2: project1 year1 returns (1 + r1), plus carried cash
    model.y2 = pyo.Constraint(
        expr=model.x1[2] + model.x3 + model.s[2]
        == (1.0 + r1) * model.x1[1] + model.s[1]
    )

    # Start of year 3: project1 year2 returns, project2 recovered (r2),
    # project3 recovered (r3), plus carried cash
    model.y3 = pyo.Constraint(
        expr=model.x1[3] + model.x4 + model.s[3]
        == (1.0 + r1) * model.x1[2] + r2 * model.x2 + r3 * model.x3 + model.s[2]
    )

    # End of year 3: final wealth
    model.end = pyo.Expression(
        expr=(1.0 + r1) * model.x1[3] + r4 * model.x4 + model.s[3]
    )

    model.obj = pyo.Objective(expr=model.end, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}
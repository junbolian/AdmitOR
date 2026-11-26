import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_fund = params["initial_fund"]
    r1 = params["return_rate_project1"]
    r2 = params["return_multiplier_project2"]
    cap2 = params["cap_project2"]
    r3 = params["return_multiplier_project3"]
    cap3 = params["cap_project3"]
    r4 = params["return_multiplier_project4"]
    cap4 = params["cap_project4"]

    model = pyo.ConcreteModel()

    # Decision variables (continuous investment amounts)
    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)  # project 1, year 1
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)  # project 1, year 2
    model.x3 = pyo.Var(domain=pyo.NonNegativeReals)  # project 1, year 3
    model.y1 = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, cap2))  # project 2
    model.y2 = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, cap3))  # project 3
    model.y3 = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, cap4))  # project 4

    # Cash-flow constraints
    model.c1 = pyo.Constraint(expr=model.x1 + model.y1 <= initial_fund)
    model.c2 = pyo.Constraint(
        expr=model.x2 + model.y2 <= (1 + r1) * model.x1
    )
    model.c3 = pyo.Constraint(
        expr=model.x3 + model.y3
        <= (1 + r1) * model.x2 + r2 * model.y1
    )
    model.c4 = pyo.Constraint(
        expr=0 <= (1 + r1) * model.x3 + r3 * model.y2 + r4 * model.y3
    )

    # Objective: wealth at end of year 3
    model.obj = pyo.Objective(
        expr=(1 + r1) * model.x3 + r3 * model.y2 + r4 * model.y3,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
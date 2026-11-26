import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    wage_s = params["wage_skilled"]
    wage_l = params["wage_laborer"]
    eff_s = params["eff_hours_skilled"]
    eff_l = params["eff_hours_laborer"]
    d1 = params["demand_task1"]
    d2 = params["demand_task2"]
    d3 = params["demand_task3"]
    max_s = params["max_skilled"]
    max_l = params["max_laborers"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.y = pyo.Var(domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=wage_s * model.x + wage_l * model.y, sense=pyo.minimize)

    model.cap_s = pyo.Constraint(expr=model.x <= max_s)
    model.cap_l = pyo.Constraint(expr=model.y <= max_l)

    model.t1 = pyo.Constraint(expr=eff_s * model.x >= d1)
    model.t2 = pyo.Constraint(expr=eff_s * model.x + eff_l * model.y >= d2)
    model.t3 = pyo.Constraint(expr=eff_s * model.x + eff_l * model.y >= d3)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
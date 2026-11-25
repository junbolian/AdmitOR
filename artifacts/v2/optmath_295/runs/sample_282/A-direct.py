import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]

    allowed = []
    for i in range(num_participants):
        for j in range(num_cars):
            if params[f"preference_{i}_{j}"] == 1:
                allowed.append((i, j))

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, num_participants - 1)
    model.C = pyo.RangeSet(0, num_cars - 1)
    model.allowed = pyo.Set(initialize=allowed, dimen=2)

    model.x = pyo.Var(model.allowed, domain=pyo.Binary)
    model.obj = pyo.Objective(expr=sum(model.x[i, j] for (i, j) in model.allowed), sense=pyo.maximize)

    def participant_rule(mm, i):
        terms = [mm.x[i, j] for j in mm.C if (i, j) in mm.allowed]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= 1
    model.participant_constraint = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(mm, j):
        terms = [mm.x[i, j] for i in mm.P if (i, j) in mm.allowed]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= 1
    model.car_constraint = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}
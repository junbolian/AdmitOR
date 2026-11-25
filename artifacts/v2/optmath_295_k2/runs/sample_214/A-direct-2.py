import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    objective_coeff = params["objective_coeff"]

    n_participants = len(preference)
    n_cars = len(preference[0])

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_participants - 1)
    model.C = pyo.RangeSet(0, n_cars - 1)
    model.PC = pyo.Set(
        initialize=[
            (i, j)
            for i in range(n_participants)
            for j in range(n_cars)
            if int(preference[i][j]) == 1
        ],
        dimen=2,
    )

    model.x = pyo.Var(model.PC, domain=pyo.Binary)

    def participant_rule(mdl, i):
        return sum(mdl.x[i, j] for j in range(n_cars) if (i, j) in mdl.PC) <= participant_capacity[i]

    def car_rule(mdl, j):
        return sum(mdl.x[i, j] for i in range(n_participants) if (i, j) in mdl.PC) <= car_capacity[j]

    model.participant_con = pyo.Constraint(model.P, rule=participant_rule)
    model.car_con = pyo.Constraint(model.C, rule=car_rule)

    model.obj = pyo.Objective(
        expr=sum(objective_coeff * model.x[i, j] for (i, j) in model.PC),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
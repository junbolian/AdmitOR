# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3]},"params":{"preference[i,j]":{"source":"params['preference'][i][j]","domain":"Binary"}},"variables":{"x[i,j]":"Binary"},"constraints":["sum(x[i,j] for j in J) <= 1 for each i in I","sum(x[i,j] for i in I) <= 1 for each j in J","x[i,j] <= preference[i,j] for each (i,j) in I x J"],"objective":{"sense":"maximize","expression":"sum(x[i,j] for i in I for j in J)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 3)
    model.J = pyo.RangeSet(0, 3)

    model.preference = pyo.Param(
        model.I,
        model.J,
        within=pyo.Binary,
        initialize={
            (i, j): params["preference"][i][j]
            for i in model.I
            for j in model.J
        },
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def participant_limit_rule(instance, i):
        return sum(instance.x[i, j] for j in instance.J) <= 1

    model.participant_limit = pyo.Constraint(
        model.I, rule=participant_limit_rule
    )

    def car_limit_rule(instance, j):
        return sum(instance.x[i, j] for i in instance.I) <= 1

    model.car_limit = pyo.Constraint(model.J, rule=car_limit_rule)

    def preference_limit_rule(instance, i, j):
        return instance.x[i, j] <= instance.preference[i, j]

    model.preference_limit = pyo.Constraint(
        model.I, model.J, rule=preference_limit_rule
    )

    model.total_assignments = pyo.Objective(
        expr=sum(model.x[i, j] for i in model.I for j in model.J),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Feasible transmission lines: (farm, substation) pairs
    lines = [
        (0, 1), (0, 2),
        (1, 0), (1, 3),
        (2, 2), (2, 3),
        (3, 1), (3, 2), (3, 3), (3, 4),
        (4, 0), (4, 1),
        (5, 3),
    ]

    farms = list(range(7))
    substations = list(range(5))

    model = pyo.ConcreteModel()

    # Decision variables: x[f, s] = 1 if farm f is matched to substation s
    model.x = pyo.Var(lines, domain=pyo.Binary)

    # Objective: maximize number of matched pairs
    model.obj = pyo.Objective(
        expr=sum(model.x[f, s] for (f, s) in lines),
        sense=pyo.maximize,
    )

    # Each solar farm dispatches to at most one substation
    def farm_rule(mdl, f):
        terms = [mdl.x[ff, s] for (ff, s) in lines if ff == f]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1
    model.farm_limit = pyo.Constraint(farms, rule=farm_rule)

    # Each substation receives from at most one solar farm
    def substation_rule(mdl, s):
        terms = [mdl.x[f, ss] for (f, ss) in lines if ss == s]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1
    model.substation_limit = pyo.Constraint(substations, rule=substation_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
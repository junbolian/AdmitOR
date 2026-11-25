# IR: {"sets":{"U":[0,1,2,3,4,5,6],"F":[0,1,2,3,4],"E":[[0,0],[0,2],[0,3],[1,4],[2,0],[2,1],[2,2],[3,0],[3,2],[3,4],[4,0],[4,2],[4,3],[4,4],[5,0]]},"params":{},"variables":{"x[u,f]":{"index":"E","type":"binary"}},"constraints":["For each u in U: sum(x[u,f] for (u,f) in E) <= 1","For each f in F: sum(x[u,f] for (u,f) in E) <= 1","Assignments exist only for pairs in E"],"objective":{"sense":"maximize","expression":"sum(x[u,f] for (u,f) in E)"}}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.U = pyo.Set(initialize=range(7), ordered=True)
    model.F = pyo.Set(initialize=range(5), ordered=True)
    model.E = pyo.Set(
        dimen=2,
        initialize=[
            (0, 0), (0, 2), (0, 3),
            (1, 4),
            (2, 0), (2, 1), (2, 2),
            (3, 0), (3, 2), (3, 4),
            (4, 0), (4, 2), (4, 3), (4, 4),
            (5, 0),
        ],
        ordered=True,
    )

    model.x = pyo.Var(model.E, domain=pyo.Binary)

    def user_capacity_rule(instance, user):
        terms = [
            instance.x[user, frequency]
            for frequency in instance.F
            if (user, frequency) in instance.E
        ]
        if not terms:
            return pyo.Constraint.Feasible
        return pyo.quicksum(terms) <= 1

    def frequency_capacity_rule(instance, frequency):
        return pyo.quicksum(
            instance.x[user, frequency]
            for user in instance.U
            if (user, frequency) in instance.E
        ) <= 1

    model.user_capacity = pyo.Constraint(
        model.U, rule=user_capacity_rule
    )
    model.frequency_capacity = pyo.Constraint(
        model.F, rule=frequency_capacity_rule
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.x[user, frequency]
            for user, frequency in model.E
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
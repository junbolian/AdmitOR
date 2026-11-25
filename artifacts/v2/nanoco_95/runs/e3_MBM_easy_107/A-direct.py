import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    mobile_users = list(range(7))
    frequencies = list(range(5))

    feasible_edges = [
        (0, 0), (0, 2), (0, 3),
        (1, 4),
        (2, 0), (2, 1), (2, 2),
        (3, 0), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 4),
        (5, 0),
    ]

    model = pyo.ConcreteModel()

    model.EDGES = pyo.Set(initialize=feasible_edges, dimen=2)

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    def user_rule(m, u):
        expr = sum(m.x[u, f] for (uu, f) in m.EDGES if uu == u)
        return expr <= 1

    def freq_rule(m, f):
        expr = sum(m.x[u, ff] for (u, ff) in m.EDGES if ff == f)
        return expr <= 1

    model.user_constr = pyo.Constraint(mobile_users, rule=user_rule)
    model.freq_constr = pyo.Constraint(frequencies, rule=freq_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[e] for e in model.EDGES),
        sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}
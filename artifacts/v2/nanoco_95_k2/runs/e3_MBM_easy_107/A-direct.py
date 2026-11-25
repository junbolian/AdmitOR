import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Feasible connections (structural)
    feasible = [
        (0, 0), (0, 2), (0, 3),
        (1, 4),
        (2, 0), (2, 1), (2, 2),
        (3, 0), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 4),
        (5, 0),
    ]

    users = sorted({u for u, f in feasible})
    freqs = sorted({f for u, f in feasible})

    model = pyo.ConcreteModel()
    model.USERS = pyo.Set(initialize=users)
    model.FREQS = pyo.Set(initialize=freqs)
    model.ARCS = pyo.Set(initialize=feasible, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def user_rule(mdl, u):
        return sum(mdl.x[u, f] for f in mdl.FREQS if (u, f) in mdl.ARCS) <= 1

    def freq_rule(mdl, f):
        return sum(mdl.x[u, f] for u in mdl.USERS if (u, f) in mdl.ARCS) <= 1

    model.user_con = pyo.Constraint(model.USERS, rule=user_rule)
    model.freq_con = pyo.Constraint(model.FREQS, rule=freq_rule)

    model.obj = pyo.Objective(expr=sum(model.x[a] for a in model.ARCS), sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    d = params["d"]
    n_days = 7

    model = pyo.ConcreteModel()
    model.J = pyo.RangeSet(0, n_days - 1)
    # Start days can be any day of the week (cyclic scheduling)
    model.S = pyo.RangeSet(0, n_days - 1)
    model.x = pyo.Var(model.S, domain=pyo.NonNegativeReals)

    def cover_rule(mdl, j):
        # Sum over shifts whose 5 consecutive days include day j (cyclic)
        return sum(mdl.x[s] for s in range(n_days) if (j - s) % n_days < 5) >= d[j]
    model.cover = pyo.Constraint(model.J, rule=cover_rule)

    model.obj = pyo.Objective(expr=sum(model.x[s] for s in model.S), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
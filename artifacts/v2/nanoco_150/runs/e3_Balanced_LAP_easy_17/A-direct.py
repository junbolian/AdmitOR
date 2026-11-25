import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cost = params["cost_matrix"]
    n = len(cost)

    model = pyo.ConcreteModel()
    model.dev = pyo.RangeSet(n)
    model.mod = pyo.RangeSet(n)

    model.x = pyo.Var(model.dev, model.mod, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i + 1, j + 1]
                   for i in range(n) for j in range(n))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.dev_assign = pyo.Constraint(
        model.dev,
        rule=lambda m, i: sum(m.x[i, j] for j in m.mod) == 1
    )

    model.mod_assign = pyo.Constraint(
        model.mod,
        rule=lambda m, j: sum(m.x[i, j] for i in m.dev) == 1
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
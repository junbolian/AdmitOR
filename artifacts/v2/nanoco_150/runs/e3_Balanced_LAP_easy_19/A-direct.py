import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    n = len(cost_matrix)
    m = len(cost_matrix[0])

    model = pyo.ConcreteModel()

    model.harvesters = pyo.RangeSet(0, n - 1)
    model.fields = pyo.RangeSet(0, m - 1)

    model.x = pyo.Var(model.harvesters, model.fields, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i, j]
                   for i in mdl.harvesters for j in mdl.fields)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def harvester_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.fields) == 1

    model.harvester_assign = pyo.Constraint(model.harvesters, rule=harvester_rule)

    def field_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.harvesters) == 1

    model.field_assign = pyo.Constraint(model.fields, rule=field_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}
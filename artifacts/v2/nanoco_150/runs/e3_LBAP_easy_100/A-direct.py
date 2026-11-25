import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)

    model = pyo.ConcreteModel()

    model.machinists = pyo.RangeSet(0, n - 1)
    model.jobs = pyo.RangeSet(0, n - 1)

    model.assign = pyo.Var(
        model.machinists, model.jobs, domain=pyo.Binary
    )
    model.T = pyo.Var(domain=pyo.NonNegativeReals)

    def machinist_rule(m, i):
        return sum(m.assign[i, j] for j in m.jobs) == 1

    def job_rule(m, j):
        return sum(m.assign[i, j] for i in m.machinists) == 1

    def bottleneck_rule(m, i, j):
        return m.T >= cost_matrix[i][j] * m.assign[i, j]

    model.machinist_con = pyo.Constraint(model.machinists, rule=machinist_rule)
    model.job_con = pyo.Constraint(model.jobs, rule=job_rule)
    model.bottleneck_con = pyo.Constraint(
        model.machinists, model.jobs, rule=bottleneck_rule
    )

    model.obj = pyo.Objective(expr=model.T, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}
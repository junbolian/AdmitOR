import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n_tech = len(cost_matrix)
    n_jobs = len(cost_matrix[0])

    model = pyo.ConcreteModel()
    model.tech = pyo.RangeSet(0, n_tech - 1)
    model.job = pyo.RangeSet(0, n_jobs - 1)

    model.x = pyo.Var(model.tech, model.job, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost_matrix[t][j] * m.x[t, j] for t in m.tech for j in m.job)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def tech_rule(m, t):
        return sum(m.x[t, j] for j in m.job) == 1

    model.tech_constraint = pyo.Constraint(model.tech, rule=tech_rule)

    def job_rule(m, j):
        return sum(m.x[t, j] for t in m.tech) == 1

    model.job_constraint = pyo.Constraint(model.job, rule=job_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
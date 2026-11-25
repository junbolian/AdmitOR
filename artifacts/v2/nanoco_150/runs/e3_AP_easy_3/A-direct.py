import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_workers = len(cost_matrix)
    num_tasks = len(cost_matrix[0])

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(num_workers)
    model.T = pyo.RangeSet(num_tasks)

    model.x = pyo.Var(model.W, model.T, within=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i + 1, j + 1]
                   for i in range(num_workers) for j in range(num_tasks))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def worker_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.T) == 1

    model.worker_constraint = pyo.Constraint(model.W, rule=worker_rule)

    def task_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.W) == 1

    model.task_constraint = pyo.Constraint(model.T, rule=task_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_workers = int(params["num_workers"])
    num_tasks = int(params["num_tasks"])

    model = pyo.ConcreteModel()

    model.workers = pyo.RangeSet(0, num_workers - 1)
    model.tasks = pyo.RangeSet(0, num_tasks - 1)

    def cost_init(mdl, i, j):
        return cost_matrix[i][j]

    model.cost = pyo.Param(model.workers, model.tasks, initialize=cost_init)

    model.x = pyo.Var(model.workers, model.tasks, domain=pyo.Binary)

    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    def worker_assign_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.tasks) == 1

    model.worker_assign = pyo.Constraint(model.workers, rule=worker_assign_rule)

    def task_assign_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.workers) == 1

    model.task_assign = pyo.Constraint(model.tasks, rule=task_assign_rule)

    def bottleneck_rule(mdl, i, j):
        return mdl.cost[i, j] * mdl.x[i, j] <= mdl.z

    model.bottleneck = pyo.Constraint(
        model.workers, model.tasks, rule=bottleneck_rule
    )

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
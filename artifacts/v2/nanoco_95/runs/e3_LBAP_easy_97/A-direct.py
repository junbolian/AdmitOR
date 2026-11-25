import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_workers = len(cost_matrix)
    num_tasks = len(cost_matrix[0])

    model = pyo.ConcreteModel()

    model.workers = pyo.RangeSet(0, num_workers - 1)
    model.tasks = pyo.RangeSet(0, num_tasks - 1)

    model.x = pyo.Var(model.workers, model.tasks, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.Reals)

    model.assignment_worker = pyo.Constraint(
        model.workers,
        rule=lambda m, i: sum(m.x[i, j] for j in m.tasks) == 1,
    )
    model.assignment_task = pyo.Constraint(
        model.tasks,
        rule=lambda m, j: sum(m.x[i, j] for i in m.workers) == 1,
    )

    def bottleneck_rule(m, i, j):
        return cost_matrix[i][j] * m.x[i, j] <= m.z

    model.bottleneck = pyo.Constraint(model.workers, model.tasks, rule=bottleneck_rule)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
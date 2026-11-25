import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_workers = int(params["num_workers"])
    num_tasks = int(params["num_tasks"])

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, num_workers - 1)
    model.T = pyo.RangeSet(0, num_tasks - 1)

    model.z = pyo.Var(model.W, model.T, domain=pyo.Binary)
    model.tmax = pyo.Var(domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=model.tmax, sense=pyo.minimize)

    def assign_server_rule(mdl, i):
        return sum(mdl.z[i, j] for j in mdl.T) == 1
    model.assign_server = pyo.Constraint(model.W, rule=assign_server_rule)

    def assign_task_rule(mdl, j):
        return sum(mdl.z[i, j] for i in mdl.W) == 1
    model.assign_task = pyo.Constraint(model.T, rule=assign_task_rule)

    def bottleneck_rule(mdl, i, j):
        return mdl.tmax >= cost_matrix[i][j] * mdl.z[i, j]
    model.bottleneck = pyo.Constraint(model.W, model.T, rule=bottleneck_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or failed: " + str(exc)}

    return {"objective": obj_val, "status": "optimal"}
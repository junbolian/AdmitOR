import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    resource_usage = params["resource_usage"]
    cost = params["cost"]

    num_vms = len(resource_usage)
    num_tasks = len(resource_usage[0])
    vms = list(range(num_vms))
    tasks = list(range(num_tasks))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(vms, tasks, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in vms for j in tasks)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(mdl, j):
        return sum(mdl.x[i, j] for i in vms) == 1

    model.assign = pyo.Constraint(tasks, rule=assign_rule)

    def capacity_rule(mdl, i):
        return sum(resource_usage[i][j] * mdl.x[i, j] for j in tasks) <= capacity[i]

    model.capacity_con = pyo.Constraint(vms, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
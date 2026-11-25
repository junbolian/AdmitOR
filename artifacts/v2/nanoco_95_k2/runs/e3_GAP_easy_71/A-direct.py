import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    resource_usage = params["resource_usage"]
    cost = params["cost"]

    num_vms = len(resource_usage)
    num_tasks = len(resource_usage[0])

    vm_names = ["VM1", "VM2", "VM3"][:num_vms]
    task_names = ["Task%d" % (j + 1) for j in range(num_tasks)]

    model = pyo.ConcreteModel()

    model.VM = pyo.Set(initialize=vm_names)
    model.TASK = pyo.Set(initialize=task_names)

    model.x = pyo.Var(model.VM, model.TASK, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(
            cost[i][j] * model.x[vm_names[i], task_names[j]]
            for i in range(num_vms)
            for j in range(num_tasks)
        ),
        sense=pyo.minimize,
    )

    model.assign_once = pyo.ConstraintList()
    for j in range(num_tasks):
        model.assign_once.add(
            sum(model.x[vm_names[i], task_names[j]] for i in range(num_vms)) == 1
        )

    model.capacity_limit = pyo.ConstraintList()
    for i in range(num_vms):
        model.capacity_limit.add(
            sum(
                resource_usage[i][j] * model.x[vm_names[i], task_names[j]]
                for j in range(num_tasks)
            )
            <= capacity[i]
        )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
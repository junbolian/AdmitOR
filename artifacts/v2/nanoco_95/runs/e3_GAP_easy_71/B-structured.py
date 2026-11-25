# IR: {"sets":{"VM":["VM1","VM2","VM3"],"TASK":[1,2,3,4,5,6,7]},"params":{"capacity_VM1":"scalar","capacity_VM2":"scalar","capacity_VM3":"scalar","usage_VM1":"array indexed by task-1","usage_VM2":"array indexed by task-1","usage_VM3":"array indexed by task-1","cost_VM1":"array indexed by task-1","cost_VM2":"array indexed by task-1","cost_VM3":"array indexed by task-1"},"variables":{"assignment[vm,task]":"binary"},"constraints":["For each task: sum_vm assignment[vm,task] = 1","For each vm: sum_task usage_vm[task-1]*assignment[vm,task] <= capacity_vm"],"objective":"minimize sum_vm,task cost_vm[task-1]*assignment[vm,task]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = {
        "VM1": params["capacity_VM1"],
        "VM2": params["capacity_VM2"],
        "VM3": params["capacity_VM3"],
    }
    usages = {
        "VM1": params["usage_VM1"],
        "VM2": params["usage_VM2"],
        "VM3": params["usage_VM3"],
    }
    costs = {
        "VM1": params["cost_VM1"],
        "VM2": params["cost_VM2"],
        "VM3": params["cost_VM3"],
    }

    model = pyo.ConcreteModel()
    model.VM = pyo.Set(initialize=["VM1", "VM2", "VM3"], ordered=True)
    model.TASK = pyo.RangeSet(1, 7)

    model.capacity = pyo.Param(model.VM, initialize=capacities)
    model.resource_usage = pyo.Param(
        model.VM,
        model.TASK,
        initialize={
            (vm, task): usages[vm][task - 1]
            for vm in model.VM
            for task in model.TASK
        },
    )
    model.assignment_cost = pyo.Param(
        model.VM,
        model.TASK,
        initialize={
            (vm, task): costs[vm][task - 1]
            for vm in model.VM
            for task in model.TASK
        },
    )

    # A value of one explicitly assigns the indexed task to the indexed VM.
    model.assignment = pyo.Var(model.VM, model.TASK, domain=pyo.Binary)

    def assign_once_rule(mdl, task):
        return sum(mdl.assignment[vm, task] for vm in mdl.VM) == 1

    model.assign_once = pyo.Constraint(model.TASK, rule=assign_once_rule)

    def capacity_limit_rule(mdl, vm):
        return (
            sum(
                mdl.resource_usage[vm, task] * mdl.assignment[vm, task]
                for task in mdl.TASK
            )
            <= mdl.capacity[vm]
        )

    model.capacity_limit = pyo.Constraint(model.VM, rule=capacity_limit_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[vm, task] * model.assignment[vm, task]
            for vm in model.VM
            for task in model.TASK
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
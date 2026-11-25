# IR: {"sets":{"VMs":[0,1,2],"Tasks":[0,1,2,3,4,5,6]},"params":{"capacity":"params['capacity'][v]","resource_usage":"params['resource_usage'][v][t]","cost":"params['cost'][v][t]"},"variables":{"assignment[v,t]":"Binary; 1 assigns task t+1 to VM v+1"},"constraints":["For each task t: sum_v assignment[v,t] == 1","For each VM v: sum_t resource_usage[v,t]*assignment[v,t] <= capacity[v]"],"objective":"Minimize sum_v sum_t cost[v,t]*assignment[v,t]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the three-VM, seven-task minimum-cost assignment problem.

    Input arrays use zero-based indexing: rows identify VMs, and columns
    identify tasks. The binary assignment variables explicitly represent
    the selected VM for every task.
    """
    capacity = params["capacity"]
    resource_usage = params["resource_usage"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.VMs = pyo.RangeSet(0, 2)
    model.Tasks = pyo.RangeSet(0, 6)

    model.vm_capacity = pyo.Param(
        model.VMs,
        initialize=lambda mdl, vm: capacity[vm],
        within=pyo.NonNegativeReals,
    )
    model.task_resource = pyo.Param(
        model.VMs,
        model.Tasks,
        initialize=lambda mdl, vm, task: resource_usage[vm][task],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.VMs,
        model.Tasks,
        initialize=lambda mdl, vm, task: cost[vm][task],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.VMs,
        model.Tasks,
        domain=pyo.Binary,
    )

    def task_assignment_rule(mdl, task):
        return sum(mdl.assignment[vm, task] for vm in mdl.VMs) == 1

    model.task_assignment = pyo.Constraint(
        model.Tasks,
        rule=task_assignment_rule,
    )

    def capacity_limit_rule(mdl, vm):
        return (
            sum(
                mdl.task_resource[vm, task] * mdl.assignment[vm, task]
                for task in mdl.Tasks
            )
            <= mdl.vm_capacity[vm]
        )

    model.capacity_limit = pyo.Constraint(
        model.VMs,
        rule=capacity_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[vm, task] * model.assignment[vm, task]
            for vm in model.VMs
            for task in model.Tasks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
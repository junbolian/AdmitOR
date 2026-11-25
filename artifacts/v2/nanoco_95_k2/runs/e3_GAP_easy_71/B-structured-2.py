# IR: {"sets":{"VM":[0,1,2],"TASK":[0,1,2,3,4,5,6]},"params":{"capacity":"capacity[i] from params['capacity']","resource_usage":"resource_usage[i][j] from params['resource_usage']","cost":"cost[i][j] from params['cost']"},"variables":{"assignment[i,j]":"binary; 1 iff task j is assigned to VM i"},"constraints":["For each task j: sum_i assignment[i,j] == 1","For each VM i: sum_j resource_usage[i][j]*assignment[i,j] <= capacity[i]"],"objective":"Minimize sum_i sum_j cost[i][j]*assignment[i,j]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    resource_usage = params["resource_usage"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.VM = pyo.RangeSet(0, 2)
    model.TASK = pyo.RangeSet(0, 6)

    model.capacity_limit = pyo.Param(
        model.VM,
        initialize={i: capacity[i] for i in model.VM},
    )
    model.task_resource = pyo.Param(
        model.VM,
        model.TASK,
        initialize={
            (i, j): resource_usage[i][j]
            for i in model.VM
            for j in model.TASK
        },
    )
    model.assignment_cost = pyo.Param(
        model.VM,
        model.TASK,
        initialize={
            (i, j): cost[i][j]
            for i in model.VM
            for j in model.TASK
        },
    )

    model.assignment = pyo.Var(model.VM, model.TASK, domain=pyo.Binary)

    def assign_once_rule(instance, j):
        return sum(
            instance.assignment[i, j] for i in instance.VM
        ) == 1

    model.assign_once = pyo.Constraint(
        model.TASK, rule=assign_once_rule
    )

    def capacity_rule(instance, i):
        return sum(
            instance.task_resource[i, j] * instance.assignment[i, j]
            for j in instance.TASK
        ) <= instance.capacity_limit[i]

    model.capacity_constraint = pyo.Constraint(
        model.VM, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.assignment[i, j]
            for i in model.VM
            for j in model.TASK
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
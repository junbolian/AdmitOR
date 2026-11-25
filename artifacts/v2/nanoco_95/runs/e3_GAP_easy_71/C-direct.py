import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = [
        params["capacity_VM1"],
        params["capacity_VM2"],
        params["capacity_VM3"],
    ]
    usage = [
        params["usage_VM1"],
        params["usage_VM2"],
        params["usage_VM3"],
    ]
    cost = [
        params["cost_VM1"],
        params["cost_VM2"],
        params["cost_VM3"],
    ]

    num_vms = 3
    num_tasks = 7
    vms = range(num_vms)
    tasks = range(num_tasks)

    model = gp.Model("task_scheduling")
    model.setParam("OutputFlag", 0)

    # x[v, t] = 1 if task t is assigned to VM v
    x = model.addVars(vms, tasks, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[v][t] * x[v, t] for v in vms for t in tasks),
        GRB.MINIMIZE,
    )

    # Each task assigned to exactly one VM
    for t in tasks:
        model.addConstr(
            gp.quicksum(x[v, t] for v in vms) == 1,
            name=f"assign_task_{t}",
        )

    # Capacity constraints per VM
    for v in vms:
        model.addConstr(
            gp.quicksum(usage[v][t] * x[v, t] for t in tasks) <= capacity[v],
            name=f"capacity_vm_{v}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}
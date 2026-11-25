import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]            # list of length 3 (VM1, VM2, VM3)
    resource_usage = params["resource_usage"]  # 3x7 matrix, rows=VMs, cols=Tasks
    cost = params["cost"]                      # 3x7 matrix, rows=VMs, cols=Tasks

    num_vms = 3
    num_tasks = 7

    model = gp.Model("task_assignment")
    model.Params.OutputFlag = 0

    x = model.addVars(num_vms, num_tasks, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(num_vms)
            for j in range(num_tasks)
        ),
        GRB.MINIMIZE,
    )

    for j in range(num_tasks):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_vms)) == 1,
            name=f"assign_{j}",
        )

    for i in range(num_vms):
        model.addConstr(
            gp.quicksum(resource_usage[i][j] * x[i, j] for j in range(num_tasks))
            <= capacity[i],
            name=f"cap_{i}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}
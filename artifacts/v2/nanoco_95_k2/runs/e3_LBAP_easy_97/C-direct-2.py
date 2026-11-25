import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_workers = params["num_workers"]
    num_tasks = params["num_tasks"]

    model = gp.Model("hft_bottleneck_assignment")
    model.Params.OutputFlag = 0

    # Assignment variables: x[i, j] == 1 iff server i is assigned feed j
    x = model.addVars(
        range(num_workers), range(num_tasks),
        vtype=GRB.BINARY, name="x"
    )

    # Bottleneck variable: maximum latency among assigned pairs
    z = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="z")

    # Each server gets exactly one feed
    for i in range(num_workers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_tasks)) == 1,
            name=f"server_{i}"
        )

    # Each feed is processed by exactly one server
    for j in range(num_tasks):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_workers)) == 1,
            name=f"feed_{j}"
        )

    # Bottleneck link: z >= cost[i, j] whenever x[i, j] == 1
    for i in range(num_workers):
        for j in range(num_tasks):
            model.addConstr(
                z >= cost_matrix[i][j] * x[i, j],
                name=f"link_{i}_{j}"
            )

    model.setObjective(z, GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    return {"objective": None, "status": f"gurobi_status_{model.status}"}
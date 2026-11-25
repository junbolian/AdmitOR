import gurobipy as gp
from gurobipy import GRB

def solve(params):
    proc_time = params["proc_time"]
    robot_assignment = params["robot_assignment"]

    num_tasks = 3
    num_stages = 3
    tasks = range(num_tasks)
    stages = range(num_stages)

    # Big-M for disjunctive constraints
    M = 100000

    model = gp.Model("robot_scheduling")
    model.setParam("OutputFlag", 0)

    # Start times: s[i][k] = start time of task i at stage k
    s = [[model.addVar(lb=0, name=f"s_{i}_{k}") for k in stages] for i in tasks]

    # Makespan
    makespan = model.addVar(lb=0, name="makespan")

    # Precedence within each task: stage k must finish before stage k+1 starts
    for i in tasks:
        for k in range(num_stages - 1):
            model.addConstr(
                s[i][k] + proc_time[i][k] <= s[i][k + 1],
                name=f"prec_{i}_{k}"
            )

    # Makespan must be >= completion of last stage of every task
    for i in tasks:
        model.addConstr(
            s[i][num_stages - 1] + proc_time[i][num_stages - 1] <= makespan,
            name=f"makespan_{i}"
        )

    # Disjunctive constraints: no two operations on the same robot can overlap
    # For each pair of operations (i,k) and (j,l) that share the same robot
    # Binary variable y[(i,k,j,l)] = 1 if (i,k) comes before (j,l)
    y = {}
    for i in tasks:
        for k in stages:
            for j in tasks:
                for l in stages:
                    if (i, k) < (j, l):  # avoid duplicates
                        if robot_assignment[i][k] == robot_assignment[j][l]:
                            var = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{k}_{j}_{l}")
                            y[(i, k, j, l)] = var

    for (i, k, j, l), var in y.items():
        # Either (i,k) finishes before (j,l) starts, or vice versa
        model.addConstr(
            s[i][k] + proc_time[i][k] <= s[j][l] + M * (1 - var),
            name=f"disj1_{i}_{k}_{j}_{l}"
        )
        model.addConstr(
            s[j][l] + proc_time[j][l] <= s[i][k] + M * var,
            name=f"disj2_{i}_{k}_{j}_{l}"
        )

    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}
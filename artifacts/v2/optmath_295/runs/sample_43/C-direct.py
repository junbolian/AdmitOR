import gurobipy as gp
from gurobipy import GRB


def solve(params):
    # Worker costs read from params
    costs = [
        params["worker_cost_1"],
        params["worker_cost_2"],
        params["worker_cost_3"],
        params["worker_cost_4"],
        params["worker_cost_5"],
        params["worker_cost_6"],
        params["worker_cost_7"],
        params["worker_cost_8"],
        params["worker_cost_9"],
        params["worker_cost_10"],
    ]

    # Structural coverage: which workers (1-indexed) can complete each task
    coverage = [
        [1, 2, 3, 4, 6, 9, 10],      # Task 1
        [5, 6, 8, 9, 10],            # Task 2
        [3, 4, 5, 10],               # Task 3
        [3, 5, 6],                  # Task 4
        [3, 5, 7, 9, 10],           # Task 5
        [2, 4, 6, 10],              # Task 6
        [1, 3, 4, 5, 7, 8, 9],       # Task 7
        [2, 3, 4, 5, 7, 8],          # Task 8
        [1, 3, 5, 6, 7],            # Task 9
        [1, 4, 5, 6, 9, 10],         # Task 10
        [2, 4, 5, 7, 10],           # Task 11
        [4, 5, 8, 10],              # Task 12
        [2, 3, 7, 9],               # Task 13
        [2, 4, 5, 6, 8, 9],          # Task 14
        [3, 4, 5, 6, 7, 9],          # Task 15
        [3, 4, 6, 7, 9, 10],         # Task 16
        [1, 3, 4, 5, 7],            # Task 17
        [2, 4, 5, 6, 10],           # Task 18
        [1, 6, 7, 9],               # Task 19
        [3, 6, 7, 9, 10],           # Task 20
        [4, 5, 6],                  # Task 21
        [1, 3, 4, 5, 8, 9],          # Task 22
    ]

    num_workers = 10
    num_tasks = len(coverage)

    model = gp.Model("worker_assignment")

    # Binary decision: whether to assign worker i (1-indexed)
    x = model.addVars(num_workers, vtype=GRB.BINARY, name="assign_worker")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(costs[i] * x[i] for i in range(num_workers)),
        GRB.MINIMIZE,
    )

    # Coverage constraints: each task must be covered by at least one assigned worker
    for t_idx, capable in enumerate(coverage):
        model.addConstr(
            gp.quicksum(x[w - 1] for w in capable) >= 1,
            name=f"cover_task_{t_idx + 1}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.status}"}
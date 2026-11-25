import gurobipy as gp
from gurobipy import GRB


def solve(params):
    proc_time = params["proc_time"]
    robot_assignment = params["robot_assignment"]

    n_tasks = len(proc_time)
    n_stages = len(proc_time[0]) if n_tasks > 0 else 0

    # Big-M upper bound: total processing time is a safe upper bound on makespan.
    M = sum(proc_time[i][j] for i in range(n_tasks) for j in range(n_stages)) + 1.0

    model = gp.Model("robot_coordination")
    model.Params.OutputFlag = 0

    # Start time of operation (task i, stage j)
    S = {}
    for i in range(n_tasks):
        for j in range(n_stages):
            S[i, j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"S_{i}_{j}")

    # Makespan variable
    Cmax = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="Cmax")

    # Precedence within a task: stage j+1 cannot start until stage j finishes (non-preemptive).
    for i in range(n_tasks):
        for j in range(n_stages - 1):
            model.addConstr(S[i, j + 1] >= S[i, j] + proc_time[i][j],
                            name=f"prec_{i}_{j}")

    # Makespan must be at least the completion time of the last stage of every task.
    for i in range(n_tasks):
        model.addConstr(Cmax >= S[i, n_stages - 1] + proc_time[i][n_stages - 1],
                        name=f"makespan_{i}")

    # Disjunctive (collision avoidance) constraints for operations sharing a robot.
    ops_by_robot = {}
    for i in range(n_tasks):
        for j in range(n_stages):
            r = robot_assignment[i][j]
            ops_by_robot.setdefault(r, []).append((i, j, proc_time[i][j]))

    for r, ops in ops_by_robot.items():
        for a in range(len(ops)):
            for b in range(a + 1, len(ops)):
                i1, j1, p1 = ops[a]
                i2, j2, p2 = ops[b]
                x = model.addVar(vtype=GRB.BINARY,
                                 name=f"x_{i1}_{j1}_{i2}_{j2}")
                # If x = 1: op (i1,j1) precedes op (i2,j2)
                model.addConstr(S[i1, j1] + p1 <= S[i2, j2] + M * (1 - x),
                                name=f"disj_a_{i1}_{j1}_{i2}_{j2}")
                # If x = 0: op (i2,j2) precedes op (i1,j1)
                model.addConstr(S[i2, j2] + p2 <= S[i1, j1] + M * x,
                                name=f"disj_b_{i1}_{j1}_{i2}_{j2}")

    model.setObjective(Cmax, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(Cmax.X), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}
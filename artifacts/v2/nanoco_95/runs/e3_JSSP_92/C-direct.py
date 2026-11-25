import gurobipy as gp
from gurobipy import GRB


def solve(params):
    pt = params["processing_times"]

    # Fixed robot routes per task (structural constants from problem definition)
    # Task 0: op0->R1, op1->R0, op2->R2
    # Task 1: op0->R2, op1->R1, op2->R0
    # Task 2: op0->R2, op1->R1, op2->R0
    robot_routes = [
        [1, 0, 2],
        [2, 1, 0],
        [2, 1, 0],
    ]

    n_tasks = len(pt)

    # Build operation list: (task, op_idx, robot, duration)
    ops = []
    for t in range(n_tasks):
        for o in range(len(pt[t])):
            r = robot_routes[t][o]
            d = pt[t][o]
            ops.append((t, o, r, d))

    total_dur = sum(d for (_, _, _, d) in ops)
    M_big = total_dur + 1.0

    model = gp.Model("jssp")
    model.Params.OutputFlag = 0

    # Start time variables
    s = {}
    for (t, o, r, d) in ops:
        s[t, o] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"s_{t}_{o}")

    Cmax = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="Cmax")

    # Precedence constraints within each task
    for t in range(n_tasks):
        for o in range(len(pt[t]) - 1):
            d = pt[t][o]
            model.addConstr(s[t, o + 1] >= s[t, o] + d, name=f"prec_{t}_{o}")

    # Disjunctive constraints: each robot handles at most one operation at a time
    by_robot = {}
    for (t, o, r, d) in ops:
        by_robot.setdefault(r, []).append((t, o, d))

    for r, op_list in by_robot.items():
        for i in range(len(op_list)):
            for j in range(i + 1, len(op_list)):
                t1, o1, d1 = op_list[i]
                t2, o2, d2 = op_list[j]
                y = model.addVar(vtype=GRB.BINARY, name=f"y_{t1}_{o1}_{t2}_{o2}")
                # y=1: op(t1,o1) finishes before op(t2,o2) starts
                model.addConstr(
                    s[t1, o1] + d1 <= s[t2, o2] + M_big * (1 - y),
                    name=f"disj_a_{t1}_{o1}_{t2}_{o2}"
                )
                model.addConstr(
                    s[t2, o2] + d2 <= s[t1, o1] + M_big * y,
                    name=f"disj_b_{t1}_{o1}_{t2}_{o2}"
                )

    # Makespan constraints
    for t in range(n_tasks):
        last_o = len(pt[t]) - 1
        d_last = pt[t][last_o]
        model.addConstr(Cmax >= s[t, last_o] + d_last, name=f"cm_{t}")

    model.setObjective(Cmax, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(Cmax.X), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}
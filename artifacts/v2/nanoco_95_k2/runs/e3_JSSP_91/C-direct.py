import gurobipy as gp
from gurobipy import GRB

def solve(params):
    p_0_1 = params["p_0_1"]
    p_0_0 = params["p_0_0"]
    p_0_2 = params["p_0_2"]
    p_1_1 = params["p_1_1"]
    p_1_0 = params["p_1_0"]
    p_1_2 = params["p_1_2"]
    p_2_1 = params["p_2_1"]
    p_2_0 = params["p_2_0"]
    p_2_2 = params["p_2_2"]

    # Lots: 0, 1, 2
    # Each lot has 3 steps: step 0 -> tool 1, step 1 -> tool 0, step 2 -> tool 2
    # Processing times: p[lot][step]
    # tool_seq[lot][step] = tool index
    tool_seq = {
        0: [1, 0, 2],
        1: [1, 0, 2],
        2: [1, 0, 2],
    }
    proc = {
        0: [p_0_1, p_0_0, p_0_2],
        1: [p_1_1, p_1_0, p_1_2],
        2: [p_2_1, p_2_0, p_2_2],
    }

    lots = [0, 1, 2]
    steps = [0, 1, 2]

    # Big-M: upper bound on makespan
    big_M = sum(proc[i][s] for i in lots for s in steps)

    model = gp.Model("fab_scheduling")
    model.setParam("OutputFlag", 0)

    # Start times: S[lot][step]
    S = {}
    for i in lots:
        for s in steps:
            S[i, s] = model.addVar(lb=0.0, name=f"S_{i}_{s}")

    # Makespan variable
    C_max = model.addVar(lb=0.0, name="C_max")

    # Objective
    model.setObjective(C_max, GRB.MINIMIZE)

    # Technological sequence constraints (each lot's steps must follow in order)
    for i in lots:
        for s in range(len(steps) - 1):
            model.addConstr(S[i, s + 1] >= S[i, s] + proc[i][s],
                            name=f"seq_{i}_{s}")

    # Makespan >= completion of each lot's last step
    for i in lots:
        last_s = steps[-1]
        model.addConstr(C_max >= S[i, last_s] + proc[i][last_s],
                        name=f"cmax_{i}")

    # No-overlap constraints on each tool
    # For each pair of lots (i, j) and each step (si, sj) that share the same tool,
    # either i's operation finishes before j starts, or vice versa.
    # Binary variable y[i,si,j,sj] = 1 means i precedes j on that tool.
    y = {}
    for i in lots:
        for si in steps:
            for j in lots:
                if j <= i:
                    continue
                for sj in steps:
                    if tool_seq[i][si] == tool_seq[j][sj]:
                        y[i, si, j, sj] = model.addVar(vtype=GRB.BINARY,
                                                        name=f"y_{i}_{si}_{j}_{sj}")
                        # i before j
                        model.addConstr(
                            S[j, sj] >= S[i, si] + proc[i][si] - big_M * (1 - y[i, si, j, sj]),
                            name=f"nooverlap_ij_{i}_{si}_{j}_{sj}"
                        )
                        # j before i
                        model.addConstr(
                            S[i, si] >= S[j, sj] + proc[j][sj] - big_M * y[i, si, j, sj],
                            name=f"nooverlap_ji_{i}_{si}_{j}_{sj}"
                        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}
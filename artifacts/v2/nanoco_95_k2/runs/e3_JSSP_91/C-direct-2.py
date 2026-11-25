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

    # Each lot has 3 steps: step 0 -> tool 1, step 1 -> tool 0, step 2 -> tool 2
    # lots: 0, 1, 2
    # steps: 0, 1, 2
    # tool_for_step[lot][step]: which tool is used at each step
    tool_for_step = {
        0: {0: 1, 1: 0, 2: 2},
        1: {0: 1, 1: 0, 2: 2},
        2: {0: 1, 1: 0, 2: 2},
    }

    # Processing times p[lot][step]
    proc = {
        0: {0: p_0_1, 1: p_0_0, 2: p_0_2},
        1: {0: p_1_1, 1: p_1_0, 2: p_1_2},
        2: {0: p_2_1, 1: p_2_0, 2: p_2_2},
    }

    lots = [0, 1, 2]
    steps = [0, 1, 2]

    # Big-M: upper bound on makespan
    big_M = sum(proc[i][s] for i in lots for s in steps) + 1

    model = gp.Model("fab_scheduling")
    model.setParam("OutputFlag", 0)

    # Start times: s_var[lot][step]
    s_var = {}
    for i in lots:
        for st in steps:
            s_var[i, st] = model.addVar(lb=0.0, name=f"s_{i}_{st}")

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    # Precedence constraints: each lot's steps must follow in order
    for i in lots:
        for st in range(len(steps) - 1):
            model.addConstr(
                s_var[i, st + 1] >= s_var[i, st] + proc[i][st],
                name=f"prec_{i}_{st}"
            )

    # Makespan must be >= completion of every last step
    for i in lots:
        model.addConstr(
            makespan >= s_var[i, 2] + proc[i][2],
            name=f"mkspan_{i}"
        )

    # No-overlap constraints on each tool
    # For each pair of (lot, step) combinations that use the same tool,
    # one must precede the other.
    # Binary variable y[i, si, j, sj] = 1 if (lot i, step si) precedes (lot j, step sj) on the tool
    y_var = {}

    # Collect all (lot, step) pairs grouped by tool
    from collections import defaultdict
    tool_ops = defaultdict(list)
    for i in lots:
        for st in steps:
            tool_ops[tool_for_step[i][st]].append((i, st))

    for tool_id, ops in tool_ops.items():
        for idx_a in range(len(ops)):
            for idx_b in range(idx_a + 1, len(ops)):
                i, si = ops[idx_a]
                j, sj = ops[idx_b]
                key = (i, si, j, sj)
                y_var[key] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{si}_{j}_{sj}")

                # Either (i,si) finishes before (j,sj) starts, or vice versa
                model.addConstr(
                    s_var[j, sj] >= s_var[i, si] + proc[i][si] - big_M * (1 - y_var[key]),
                    name=f"nooverlap1_{i}_{si}_{j}_{sj}"
                )
                model.addConstr(
                    s_var[i, si] >= s_var[j, sj] + proc[j][sj] - big_M * y_var[key],
                    name=f"nooverlap2_{i}_{si}_{j}_{sj}"
                )

    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}
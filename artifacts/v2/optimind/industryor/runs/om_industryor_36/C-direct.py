import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    t = {
        (1,1): params["t_11"], (1,2): params["t_12"], (1,3): params["t_13"],
        (2,1): params["t_21"], (2,2): params["t_22"], (2,3): params["t_23"],
        (3,1): params["t_31"], (3,2): params["t_32"], (3,3): params["t_33"],
    }

    products = [1, 2, 3]
    machines = [1, 2, 3]
    all_perms = list(permutations(products))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: y[p] = 1 if permutation p is chosen
    y = model.addVars(len(all_perms), vtype=GRB.BINARY, name="y")

    # Exactly one permutation is chosen
    model.addConstr(gp.quicksum(y[idx] for idx in range(len(all_perms))) == 1)

    # For each permutation, compute the makespan analytically
    # S[i][j] = start time of product at position i on machine j
    # C[i][j] = completion time
    # C[i][j] = max(C[i-1][j], C[i][j-1]) + t[perm[i]][j]

    makespan_vals = []
    for perm in all_perms:
        C = {}
        for pos in range(3):
            prod = perm[pos]
            for mach in machines:
                prev_pos_finish = C[(pos-1, mach)] if pos > 0 else 0
                prev_mach_finish = C[(pos, mach-1)] if mach > 1 else 0
                C[(pos, mach)] = max(prev_pos_finish, prev_mach_finish) + t[(prod, mach)]
        makespan_vals.append(C[(2, 3)])

    # Objective: minimize makespan over chosen permutation
    makespan_expr = gp.quicksum(makespan_vals[idx] * y[idx] for idx in range(len(all_perms)))
    model.setObjective(makespan_expr, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
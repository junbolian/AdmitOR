import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    t = {
        (1, 1): params["t_11"],
        (1, 2): params["t_12"],
        (1, 3): params["t_13"],
        (2, 1): params["t_21"],
        (2, 2): params["t_22"],
        (2, 3): params["t_23"],
        (3, 1): params["t_31"],
        (3, 2): params["t_32"],
        (3, 3): params["t_33"],
    }

    products = [1, 2, 3]
    machines = [1, 2, 3]

    best_makespan = float("inf")
    best_perm = None

    # Enumerate all 6 permutations of product order (same order on all machines)
    for perm in permutations(products):
        # Compute completion times for this sequence
        # C[i][j] = completion time of product perm[i] on machine j
        C = {}
        for idx, prod in enumerate(perm):
            for jdx, mach in enumerate(machines):
                if idx == 0 and jdx == 0:
                    C[(idx, jdx)] = t[(prod, mach)]
                elif idx == 0:
                    # First product, subsequent machines: must wait for same product on previous machine
                    C[(idx, jdx)] = C[(idx, jdx - 1)] + t[(prod, mach)]
                elif jdx == 0:
                    # First machine, subsequent products: must wait for previous product to finish machine 1
                    C[(idx, jdx)] = C[(idx - 1, jdx)] + t[(prod, mach)]
                else:
                    # Must wait for: same product on previous machine AND previous product on same machine
                    C[(idx, jdx)] = max(C[(idx - 1, jdx)], C[(idx, jdx - 1)]) + t[(prod, mach)]

        makespan = C[(len(perm) - 1, len(machines) - 1)]
        if makespan < best_makespan:
            best_makespan = makespan
            best_perm = perm

    # Now build a Gurobi model that represents the optimal permutation found
    # (the problem is a pure flow shop scheduling problem; we encode the optimal sequence)
    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)

    perm = best_perm
    n_prod = len(products)
    n_mach = len(machines)

    # Decision variables: C_vars[i][j] = completion time of product perm[i] on machine j
    C_vars = {}
    for idx in range(n_prod):
        for jdx in range(n_mach):
            C_vars[(idx, jdx)] = model.addVar(lb=0.0, name=f"C_{idx}_{jdx}")

    makespan_var = model.addVar(lb=0.0, name="makespan")
    model.setObjective(makespan_var, GRB.MINIMIZE)

    # Processing time constraints and precedence
    for idx, prod in enumerate(perm):
        for jdx, mach in enumerate(machines):
            proc = t[(prod, mach)]
            if idx == 0 and jdx == 0:
                model.addConstr(C_vars[(idx, jdx)] >= proc)
            elif idx == 0:
                model.addConstr(C_vars[(idx, jdx)] >= C_vars[(idx, jdx - 1)] + proc)
            elif jdx == 0:
                model.addConstr(C_vars[(idx, jdx)] >= C_vars[(idx - 1, jdx)] + proc)
            else:
                model.addConstr(C_vars[(idx, jdx)] >= C_vars[(idx - 1, jdx)] + proc)
                model.addConstr(C_vars[(idx, jdx)] >= C_vars[(idx, jdx - 1)] + proc)

    # Makespan = completion time of last product on last machine
    model.addConstr(makespan_var >= C_vars[(n_prod - 1, n_mach - 1)])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
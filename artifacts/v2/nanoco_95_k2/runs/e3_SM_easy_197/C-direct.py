import gurobipy as gp
from gurobipy import GRB

def solve(params):
    raw_sp = params["supplier_pref_positions"]
    raw_pp = params["plant_pref_positions"]

    n = 7

    # Normalize to plain Python lists-of-lists to avoid numpy/pandas indexing quirks
    supplier_pref = [[int(raw_sp[i][j]) for j in range(n)] for i in range(n)]
    plant_pref    = [[int(raw_pp[j][i]) for i in range(n)] for j in range(n)]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Each supplier assigned to exactly one plant
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1)

    # Each plant assigned to exactly one supplier
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1)

    # Stability: for every pair (i, j), no blocking pair may exist.
    # A_ij: plants that supplier i weakly prefers over plant j (positions <= pos of j)
    # B_ij: suppliers that plant j weakly prefers over supplier i (positions <= pos of i)
    # Constraint: sum_{j' in A_ij} x[i,j'] + sum_{i' in B_ij} x[i',j] >= 2
    for i in range(n):
        for j in range(n):
            A_ij = [jp for jp in range(n) if supplier_pref[i][jp] <= supplier_pref[i][j]]
            B_ij = [ip for ip in range(n) if plant_pref[j][ip] <= plant_pref[j][i]]
            model.addConstr(
                gp.quicksum(x[i, jp] for jp in A_ij) +
                gp.quicksum(x[ip, j] for ip in B_ij) >= 2,
                name=f"stab_{i}_{j}"
            )

    # Objective: minimize egalitarian score
    model.setObjective(
        gp.quicksum(
            (supplier_pref[i][j] + plant_pref[j][i]) * x[i, j]
            for i in range(n)
            for j in range(n)
        ),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        # Diagnose: compute IIS and report, but return infeasible
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}
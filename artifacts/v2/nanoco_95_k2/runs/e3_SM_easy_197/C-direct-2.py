import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supplier_pref = params["supplier_pref_positions"]  # supplier_pref[i][j] = rank of plant j for supplier i
    plant_pref = params["plant_pref_positions"]        # plant_pref[j][i] = rank of supplier i for plant j

    n = 7  # structural constant: number of suppliers and plants

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if supplier i is matched to plant j
    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Each supplier matched to exactly one plant
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1)

    # Each plant matched to exactly one supplier
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1)

    # Stability constraints: no blocking pair (i, j)
    # A pair (i, j) is blocking if supplier i prefers j over their current match
    # AND plant j prefers i over their current match.
    # Formally: for all i, j, it cannot be that both:
    #   - supplier i prefers j to their assigned plant (supplier_pref[i][j] < supplier_pref[i][k] for matched k)
    #   - plant j prefers i to their assigned supplier (plant_pref[j][i] < plant_pref[j][k] for matched k)
    #
    # For each potential blocking pair (i, j):
    # Let A_ij = set of plants k that supplier i likes at least as much as j (rank <= rank of j)
    # Let B_ij = set of suppliers k that plant j likes at least as much as i (rank <= rank of i)
    # Stability requires: sum_{k in A_ij} x[i,k] + sum_{k in B_ij} x[k,j] >= 1
    # (at least one of them is already matched to someone they prefer at least as much)

    for i in range(n):
        for j in range(n):
            rank_i_j = supplier_pref[i][j]  # supplier i's rank for plant j
            rank_j_i = plant_pref[j][i]     # plant j's rank for supplier i

            # Plants that supplier i weakly prefers over j (rank <= rank_i_j)
            A = [k for k in range(n) if supplier_pref[i][k] <= rank_i_j]
            # Suppliers that plant j weakly prefers over i (rank <= rank_j_i)
            B = [k for k in range(n) if plant_pref[j][k] <= rank_j_i]

            model.addConstr(
                gp.quicksum(x[i, k] for k in A) + gp.quicksum(x[k, j] for k in B) >= 1
            )

    # Objective: minimize total egalitarian score
    obj = gp.quicksum(
        (supplier_pref[i][j] + plant_pref[j][i]) * x[i, j]
        for i in range(n)
        for j in range(n)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}
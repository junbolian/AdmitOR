import gurobipy as gp
from gurobipy import GRB

def solve(params):
    men_pref = params["men_preferences"]
    women_pref = params["women_preferences"]
    num_men = params["num_men"]
    num_women = params["num_women"]

    # Build rank lookup tables
    # men_rank[i][j] = rank of woman j in man i's list (0 = most preferred)
    men_rank = {}
    for i in range(num_men):
        men_rank[i] = {}
        for rank, j in enumerate(men_pref[i]):
            men_rank[i][j] = rank

    # women_rank[j][i] = rank of man i in woman j's list
    women_rank = {}
    for j in range(num_women):
        women_rank[j] = {}
        for rank, i in enumerate(women_pref[j]):
            women_rank[j][i] = rank

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if man i is matched to woman j
    x = model.addVars(num_men, num_women, vtype=GRB.BINARY, name="x")

    # Perfect matching constraints
    for i in range(num_men):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_women)) == 1)
    for j in range(num_women):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_men)) == 1)

    # Stability constraints:
    # For every potential blocking pair (i, j) where man i is not matched to woman j:
    # They form a blocking pair if man i prefers j over his match AND woman j prefers i over her match.
    #
    # To prevent (i, j) from being a blocking pair, at least one of:
    #   (a) man i is matched to someone he prefers >= j (i.e., rank <= men_rank[i][j])
    #   (b) woman j is matched to someone she prefers >= i (i.e., rank <= women_rank[j][i])
    #
    # Formally: for each (i, j), it must NOT be the case that both:
    #   - man i is matched to some j' with men_rank[i][j'] > men_rank[i][j]
    #   - woman j is matched to some i' with women_rank[j][i'] > women_rank[j][i]
    #
    # Equivalently:
    #   sum_{j': men_rank[i][j'] <= men_rank[i][j]} x[i,j']
    #   + sum_{i': women_rank[j][i'] <= women_rank[j][i]} x[i',j]  >= 1
    #
    # (at least one side must be "happy enough" with their assigned partner)

    for i in range(num_men):
        for j in range(num_women):
            r_ij = men_rank[i][j]   # man i's rank of woman j
            r_ji = women_rank[j][i] # woman j's rank of man i

            # Women that man i likes at least as much as woman j
            men_happy = [jp for jp in range(num_women) if men_rank[i][jp] <= r_ij]
            # Men that woman j likes at least as much as man i
            women_happy = [ip for ip in range(num_men) if women_rank[j][ip] <= r_ji]

            model.addConstr(
                gp.quicksum(x[i, jp] for jp in men_happy) +
                gp.quicksum(x[ip, j] for ip in women_happy) >= 1
            )

    # Objective: minimize egalitarian score
    obj = gp.quicksum(
        (men_rank[i][j] + women_rank[j][i]) * x[i, j]
        for i in range(num_men)
        for j in range(num_women)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}
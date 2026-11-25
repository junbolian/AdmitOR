import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5

    # investor_pref[i][j] = rank that investor i gives to founder j (0 = most preferred)
    # Investor 0 ranks founders: 0,2,3,1,4
    # Investor 1 ranks founders: 1,4,2,0,3
    # Investor 2 ranks founders: 3,1,0,4,2
    # Investor 3 ranks founders: 0,4,2,1,3
    # Investor 4 ranks founders: 2,0,1,3,4
    investor_pref = [
        [0, 3, 1, 2, 4],
        [3, 0, 2, 4, 1],
        [2, 1, 4, 0, 3],
        [0, 3, 2, 4, 1],
        [1, 2, 0, 3, 4],
    ]

    # founder_pref[j][i] = rank that founder j gives to investor i (0 = most preferred)
    # Founder 0 ranks investors: 4,1,3,2,0
    # Founder 1 ranks investors: 0,3,1,2,4
    # Founder 2 ranks investors: 3,1,2,0,4
    # Founder 3 ranks investors: 2,1,4,0,3
    # Founder 4 ranks investors: 1,4,0,3,2
    founder_pref = [
        [4, 1, 3, 2, 0],
        [0, 2, 3, 1, 4],
        [3, 1, 2, 0, 4],
        [3, 1, 0, 4, 2],
        [2, 0, 4, 3, 1],
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if investor i is matched to founder j
    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Each investor matched to exactly one founder
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1)

    # Each founder matched to exactly one investor
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1)

    # Stability constraints: no blocking pair (i, j)
    # A blocking pair exists if investor i prefers founder j over their current match
    # AND founder j prefers investor i over their current match.
    # For each potential blocking pair (i, j), at least one of them must be
    # matched to someone they prefer at least as much as the other.
    #
    # Formally: for all i, j, it cannot be that both:
    #   investor i prefers j over their match, AND founder j prefers i over their match
    #
    # Equivalent: for all i, j:
    #   sum_{j': investor i prefers j' over j} x[i,j'] +
    #   sum_{i': founder j prefers i' over i} x[i',j] >= 1
    #
    # This means at least one of them is already matched to someone they prefer
    # (or to each other), preventing (i,j) from being a blocking pair.

    for i in range(n):
        for j in range(n):
            # Founders that investor i prefers over founder j (rank strictly less than rank of j)
            rank_ij = investor_pref[i][j]
            better_founders_for_i = [jp for jp in range(n) if investor_pref[i][jp] < rank_ij]

            # Investors that founder j prefers over investor i (rank strictly less than rank of i)
            rank_ji = founder_pref[j][i]
            better_investors_for_j = [ip for ip in range(n) if founder_pref[j][ip] < rank_ji]

            # Stability: at least one side is matched to someone they prefer
            # (or they are matched to each other, in which case x[i,j]=1 is in both sums
            #  if rank < rank, but actually x[i,j] itself is not in either sum)
            # We need: x[i,j] + sum_{jp in better_founders} x[i,jp] + sum_{ip in better_investors} x[ip,j] >= 1
            lhs = (gp.quicksum(x[i, jp] for jp in better_founders_for_i) +
                   gp.quicksum(x[ip, j] for ip in better_investors_for_j) +
                   x[i, j])
            model.addConstr(lhs >= 1)

    # Objective: minimize total strategic misfit index
    obj = gp.quicksum(
        (investor_pref[i][j] + founder_pref[j][i]) * x[i, j]
        for i in range(n)
        for j in range(n)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
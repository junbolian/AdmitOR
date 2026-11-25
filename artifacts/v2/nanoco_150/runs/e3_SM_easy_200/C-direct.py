import gurobipy as gp
from gurobipy import GRB

def solve(params):
    lab_preferences = params["lab_preferences"]
    site_preferences = params["site_preferences"]
    rank_index_min = params["rank_index_min"]
    rank_index_max = params["rank_index_max"]
    num_labs = params["num_labs"]
    num_sites = params["num_sites"]

    # Build rank lookup tables:
    # lab_rank[l][s] = rank that lab l gives to site s (0=best)
    # site_rank[s][l] = rank that site s gives to lab l (0=best)
    lab_rank = {}
    for l in range(num_labs):
        lab_rank[l] = {}
        for rank_pos, s in enumerate(lab_preferences[l]):
            lab_rank[l][s] = rank_pos

    site_rank = {}
    for s in range(num_sites):
        site_rank[s] = {}
        for rank_pos, l in enumerate(site_preferences[s]):
            site_rank[s][l] = rank_pos

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable x[l,s] = 1 if lab l is matched to site s
    x = {}
    for l in range(num_labs):
        for s in range(num_sites):
            x[l, s] = model.addVar(vtype=GRB.BINARY, name=f"x_{l}_{s}")

    # Each lab matched to exactly one site
    for l in range(num_labs):
        model.addConstr(
            gp.quicksum(x[l, s] for s in range(num_sites)) == 1,
            name=f"lab_assign_{l}"
        )

    # Each site matched to exactly one lab
    for s in range(num_sites):
        model.addConstr(
            gp.quicksum(x[l, s] for l in range(num_labs)) == 1,
            name=f"site_assign_{s}"
        )

    # Stability constraints:
    # For every potential blocking pair (l, s) where l is not matched to s:
    # It cannot be that lab l prefers s over its current match AND
    # site s prefers l over its current match.
    #
    # Formally: for all (l, s), if lab l prefers s to some other site s2,
    # and site s prefers l to some other lab l2, then x[l,s] must = 1.
    #
    # Equivalent formulation: for each (l, s),
    # sum_{s2: lab_rank[l][s2] < lab_rank[l][s]} x[l,s2]
    # + sum_{l2: site_rank[s][l2] < site_rank[s][l]} x[l2,s]
    # + x[l,s] >= 1
    #
    # This says: either l is matched to s, or l has a match it prefers at least
    # as much as s, or s has a match it prefers at least as much as l.
    # (Prevents (l,s) from being a blocking pair.)

    for l in range(num_labs):
        for s in range(num_sites):
            # Sites that lab l prefers over s (strictly better rank)
            better_for_lab = [
                s2 for s2 in range(num_sites)
                if lab_rank[l][s2] < lab_rank[l][s]
            ]
            # Labs that site s prefers over l (strictly better rank)
            better_for_site = [
                l2 for l2 in range(num_labs)
                if site_rank[s][l2] < site_rank[s][l]
            ]

            model.addConstr(
                x[l, s]
                + gp.quicksum(x[l, s2] for s2 in better_for_lab)
                + gp.quicksum(x[l2, s] for l2 in better_for_site)
                >= 1,
                name=f"stability_{l}_{s}"
            )

    # Objective: minimize egalitarian score (sum of mutual rank indices)
    obj = gp.quicksum(
        (lab_rank[l][s] + site_rank[s][l]) * x[l, s]
        for l in range(num_labs)
        for s in range(num_sites)
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
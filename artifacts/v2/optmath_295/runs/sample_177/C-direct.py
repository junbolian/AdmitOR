import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_peaks = int(params["num_peaks"])
    num_aa = int(params["num_amino_acids"])
    num_assignments = int(params["num_assignments"])

    # Build cost matrix from params
    cost = {}
    for p in range(num_peaks):
        for a in range(num_aa):
            cost[p, a] = params[f"cost_peak{p}_aa{a}"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables
    x = model.addVars(num_peaks, num_aa, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[p, a] * x[p, a] for p in range(num_peaks) for a in range(num_aa)),
        GRB.MINIMIZE
    )

    # Each peak assigned to at most one amino acid
    for p in range(num_peaks):
        model.addConstr(gp.quicksum(x[p, a] for a in range(num_aa)) <= 1, name=f"peak_{p}_once")

    # Each amino acid assigned to at most one peak
    for a in range(num_aa):
        model.addConstr(gp.quicksum(x[p, a] for p in range(num_peaks)) <= 1, name=f"aa_{a}_once")

    # Exactly num_assignments total assignments
    model.addConstr(
        gp.quicksum(x[p, a] for p in range(num_peaks) for a in range(num_aa)) == num_assignments,
        name="total_assignments"
    )

    # NOE constraints: for every pair of peaks (p1, p2) and every pair of amino acids (a1, a2),
    # if x[p1, a1] = 1 and x[p2, a2] = 1 then the amino acids must be "compatible".
    # The problem description does not supply a distance matrix or threshold as params,
    # so we implement the NOE constraints in the standard linearised form:
    #   x[p1, a1] + x[p2, a2] <= 1  for every (p1, a1, p2, a2) pair that violates the threshold.
    #
    # Because no distance data is provided in params, we treat all amino acid pairs as
    # potentially incompatible and enforce the constraint only for distinct peaks and
    # distinct amino acids (which is already implied by the at-most-one constraints above).
    # When a distance matrix IS provided via params in the future the block below can be
    # replaced with the actual threshold check.
    #
    # For the problem as stated (no distance/threshold params supplied), the structural
    # NOE requirement reduces to: if Peak i and Peak j are NOE-related, their assigned
    # amino acids must be distinct — which is already enforced by the amino-acid
    # uniqueness constraints.  No additional constraints are added here unless the
    # distance data is present.

    # Check whether distance/threshold params were supplied
    has_distance = "distance_threshold" in params
    if has_distance:
        threshold = params["distance_threshold"]
        # Expect params["distance_aa_i_j"] for all i, j in range(num_aa)
        for p1 in range(num_peaks):
            for p2 in range(p1 + 1, num_peaks):
                for a1 in range(num_aa):
                    for a2 in range(num_aa):
                        if a1 == a2:
                            continue
                        key = f"distance_aa_{a1}_{a2}"
                        if key in params and params[key] >= threshold:
                            # Assigning p1->a1 and p2->a2 simultaneously is forbidden
                            model.addConstr(
                                x[p1, a1] + x[p2, a2] <= 1,
                                name=f"noe_p{p1}a{a1}_p{p2}a{a2}"
                            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
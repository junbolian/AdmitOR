import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    total_assignments = params["total_assignments"]
    noe_thresholds = params["noe_thresholds"]

    num_peaks = 4
    num_amino_acids = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if peak i assigned to amino acid j
    x = {}
    for i in range(num_peaks):
        for j in range(num_amino_acids):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j]
                    for i in range(num_peaks)
                    for j in range(num_amino_acids)),
        GRB.MINIMIZE
    )

    # Each amino acid assigned to at most one peak
    for j in range(num_amino_acids):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1,
            name=f"amino_acid_{j}_atmost_one"
        )

    # Each peak assigned to at most one amino acid
    for i in range(num_peaks):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1,
            name=f"peak_{i}_atmost_one"
        )

    # Exactly total_assignments assignments in total
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)) == total_assignments,
        name="total_assignments"
    )

    # NOE spatial consistency constraints.
    # noe_thresholds can be:
    #   - a dict mapping (p1, a1, p2, a2) -> threshold value
    #   - a list/tuple of entries, where each entry is either:
    #       * a tuple/list of (p1, a1, p2, a2, threshold)
    #       * a tuple/list of (p1, a1, p2, a2) with threshold implied as 0
    #   - a 2D array/list indexed by (a1, a2) giving thresholds, with constraints
    #     applied to all peak pairs
    # The constraint: if assigning peak p1->a1 and peak p2->a2 simultaneously violates
    # the NOE distance threshold (threshold <= 0 means forbidden), add x[p1,a1]+x[p2,a2]<=1.

    if isinstance(noe_thresholds, dict):
        for key, threshold in noe_thresholds.items():
            if hasattr(key, '__len__') and len(key) == 4:
                p1, a1, p2, a2 = key
                if threshold <= 0:
                    model.addConstr(
                        x[p1, a1] + x[p2, a2] <= 1,
                        name=f"noe_{p1}_{a1}_{p2}_{a2}"
                    )
    elif isinstance(noe_thresholds, (list, tuple)):
        # Check if it looks like a 2D matrix (list of lists of numbers)
        # or a list of constraint tuples
        if len(noe_thresholds) > 0:
            first = noe_thresholds[0]
            # If the first element is a list/tuple of numbers (not a nested structure of tuples),
            # treat as 2D amino acid distance matrix
            if isinstance(first, (list, tuple)) and len(first) > 0 and isinstance(first[0], (int, float)):
                # 2D matrix: noe_thresholds[a1][a2] = threshold
                # Apply to all peak pairs (p1, p2) with p1 != p2
                for a1 in range(len(noe_thresholds)):
                    for a2 in range(len(noe_thresholds[a1])):
                        threshold = noe_thresholds[a1][a2]
                        if threshold <= 0:
                            for p1 in range(num_peaks):
                                for p2 in range(num_peaks):
                                    if p1 != p2 and a1 != a2:
                                        model.addConstr(
                                            x[p1, a1] + x[p2, a2] <= 1,
                                            name=f"noe_{p1}_{a1}_{p2}_{a2}"
                                        )
            elif isinstance(first, (list, tuple)):
                # List of tuples: each entry is (p1, a1, p2, a2, threshold) or (p1, a1, p2, a2)
                for entry in noe_thresholds:
                    if isinstance(entry, (list, tuple)):
                        if len(entry) == 5:
                            p1, a1, p2, a2, threshold = entry
                            if threshold <= 0:
                                model.addConstr(
                                    x[p1, a1] + x[p2, a2] <= 1,
                                    name=f"noe_{p1}_{a1}_{p2}_{a2}"
                                )
                        elif len(entry) == 4:
                            p1, a1, p2, a2 = entry
                            model.addConstr(
                                x[p1, a1] + x[p2, a2] <= 1,
                                name=f"noe_{p1}_{a1}_{p2}_{a2}"
                            )
            elif isinstance(first, (int, float)):
                # Flat list of numbers — interpret as flattened matrix over amino acid pairs
                # noe_thresholds[a1 * num_amino_acids + a2] = threshold
                for a1 in range(num_amino_acids):
                    for a2 in range(num_amino_acids):
                        idx = a1 * num_amino_acids + a2
                        if idx < len(noe_thresholds):
                            threshold = noe_thresholds[idx]
                            if threshold <= 0:
                                for p1 in range(num_peaks):
                                    for p2 in range(num_peaks):
                                        if p1 != p2 and a1 != a2:
                                            model.addConstr(
                                                x[p1, a1] + x[p2, a2] <= 1,
                                                name=f"noe_{p1}_{a1}_{p2}_{a2}"
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
        return {"objective": None, "status": f"status_{status}"}
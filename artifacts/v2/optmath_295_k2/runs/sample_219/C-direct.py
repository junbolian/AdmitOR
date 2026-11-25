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

    x = {}
    for i in range(num_peaks):
        for j in range(num_amino_acids):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j]
                    for i in range(num_peaks)
                    for j in range(num_amino_acids)),
        GRB.MINIMIZE
    )

    for j in range(num_amino_acids):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1,
            name=f"aa_{j}_atmost_one"
        )

    for i in range(num_peaks):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1,
            name=f"peak_{i}_atmost_one"
        )

    model.addConstr(
        gp.quicksum(x[i, j]
                    for i in range(num_peaks)
                    for j in range(num_amino_acids)) == total_assignments,
        name="total_assignments_constr"
    )

    # NOE constraints: noe_thresholds is a dict keyed by (i1, j1, i2, j2) or (j1, j2)
    # For each entry, if the threshold is exceeded (or the entry signals incompatibility),
    # the co-assignment is forbidden: x[i1,j1] + x[i2,j2] <= 1
    # We try both key formats and treat presence of a finite threshold as a violation flag.
    if isinstance(noe_thresholds, dict):
        for key, threshold in noe_thresholds.items():
            if threshold is None:
                continue
            if len(key) == 4:
                # Key is (i1, j1, i2, j2)
                i1, j1, i2, j2 = key
                if i1 != i2 and j1 != j2:
                    model.addConstr(
                        x[i1, j1] + x[i2, j2] <= 1,
                        name=f"noe_{i1}_{j1}_{i2}_{j2}"
                    )
            elif len(key) == 2:
                # Key is (j1, j2) — applies to all peak pairs
                j1, j2 = key
                if j1 != j2:
                    for i1 in range(num_peaks):
                        for i2 in range(num_peaks):
                            if i1 != i2:
                                model.addConstr(
                                    x[i1, j1] + x[i2, j2] <= 1,
                                    name=f"noe_aa_{j1}_{j2}_{i1}_{i2}"
                                )
    elif noe_thresholds is not None:
        # 2D array: noe_thresholds[j1][j2] = threshold or None
        for j1 in range(num_amino_acids):
            for j2 in range(num_amino_acids):
                if j1 == j2:
                    continue
                try:
                    threshold = noe_thresholds[j1][j2]
                except (IndexError, KeyError, TypeError):
                    threshold = None
                if threshold is not None:
                    for i1 in range(num_peaks):
                        for i2 in range(num_peaks):
                            if i1 != i2:
                                model.addConstr(
                                    x[i1, j1] + x[i2, j2] <= 1,
                                    name=f"noe_aa_{j1}_{j2}_{i1}_{i2}"
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
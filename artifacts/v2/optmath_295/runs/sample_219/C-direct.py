import gurobipy as gp
from gurobipy import GRB


def solve(params):
    costs_raw = params["costs"]
    total_assignments = params["total_assignments"]

    # costs may be a flat list, list-of-lists, or dict-of-dicts
    # Normalize to a 2D list indexed by [i][j]
    if isinstance(costs_raw, dict):
        # dict of dicts: {i: {j: cost}}
        peak_indices = sorted(costs_raw.keys())
        aa_indices = sorted(costs_raw[peak_indices[0]].keys())
        n_peaks = len(peak_indices)
        n_aas = len(aa_indices)
        costs = [
            [costs_raw[peak_indices[i]][aa_indices[j]] for j in range(n_aas)]
            for i in range(n_peaks)
        ]
    elif isinstance(costs_raw, (list, tuple)):
        first = costs_raw[0]
        if isinstance(first, (list, tuple)):
            # list of lists
            n_peaks = len(costs_raw)
            n_aas = len(costs_raw[0])
            costs = [list(row) for row in costs_raw]
        elif isinstance(first, dict):
            # list of dicts: [{j: cost}, ...]
            n_peaks = len(costs_raw)
            aa_indices = sorted(costs_raw[0].keys())
            n_aas = len(aa_indices)
            costs = [
                [costs_raw[i][aa_indices[j]] for j in range(n_aas)]
                for i in range(n_peaks)
            ]
        else:
            # flat list of length n_peaks * n_aas; infer shape from known 4x5
            # fall back: treat as flat, need n_aas from params or default to 5
            n_aas = int(params.get("n_aas", 5))
            total_len = len(costs_raw)
            n_peaks = total_len // n_aas
            costs = [
                [costs_raw[i * n_aas + j] for j in range(n_aas)]
                for i in range(n_peaks)
            ]
    else:
        raise TypeError(f"Unsupported costs type: {type(costs_raw)}")

    model = gp.Model("spectral_peak_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i, j] = 1 if peak i is assigned to amino acid j
    x = {}
    for i in range(n_peaks):
        for j in range(n_aas):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(
            costs[i][j] * x[i, j]
            for i in range(n_peaks)
            for j in range(n_aas)
        ),
        GRB.MINIMIZE,
    )

    # Each amino acid assigned to at most one peak
    for j in range(n_aas):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_peaks)) <= 1,
            name=f"aa_{j}_at_most_one",
        )

    # Each peak assigned to at most one amino acid
    for i in range(n_peaks):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_aas)) <= 1,
            name=f"peak_{i}_at_most_one",
        )

    # Exactly total_assignments assignments
    model.addConstr(
        gp.quicksum(
            x[i, j] for i in range(n_peaks) for j in range(n_aas)
        ) == total_assignments,
        name="total_assignments_constr",
    )

    # NOE constraints (format 1): list of tuples (i1, j1, i2, j2[, dist, threshold])
    noe_constraints = params.get("noe_constraints", [])
    for idx, constraint in enumerate(noe_constraints):
        if len(constraint) >= 6:
            i1, j1, i2, j2, dist, thresh = constraint[:6]
            if dist >= thresh:
                model.addConstr(
                    x[i1, j1] + x[i2, j2] <= 1,
                    name=f"noe_{idx}_{i1}_{j1}_{i2}_{j2}",
                )
        else:
            i1, j1, i2, j2 = constraint[:4]
            model.addConstr(
                x[i1, j1] + x[i2, j2] <= 1,
                name=f"noe_{idx}_{i1}_{j1}_{i2}_{j2}",
            )

    # NOE constraints (format 2): distance matrix + threshold + pairs
    aa_distances = params.get("aa_distances")
    noe_threshold = params.get("noe_threshold")
    noe_pairs = params.get("noe_pairs", [])

    if aa_distances is not None and noe_threshold is not None:
        for idx, (i1, j1, i2, j2) in enumerate(noe_pairs):
            if aa_distances[j1][j2] >= noe_threshold:
                model.addConstr(
                    x[i1, j1] + x[i2, j2] <= 1,
                    name=f"noe_dist_{idx}_{i1}_{j1}_{i2}_{j2}",
                )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    peak_count = int(params["peak_count"])
    amino_acid_count = int(params["amino_acid_count"])
    required_assignments = int(params["required_assignments"])
    cost_matrix = params["cost_matrix"]
    noe_pairs = params["noe_pairs"]

    model = gp.Model("peak_amino_assignment")
    model.Params.OutputFlag = 0

    # Decision variables: x[i, j] = 1 if peak i is assigned to amino acid j
    x = {}
    for i in range(peak_count):
        for j in range(amino_acid_count):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name="x_%d_%d" % (i, j))

    model.update()

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(
            cost_matrix[i][j] * x[i, j]
            for i in range(peak_count)
            for j in range(amino_acid_count)
        ),
        GRB.MINIMIZE,
    )

    # Each peak assigned to at most one amino acid
    for i in range(peak_count):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(amino_acid_count)) <= 1,
            name="peak_cap_%d" % i,
        )

    # Each amino acid receives at most one peak
    for j in range(amino_acid_count):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(peak_count)) <= 1,
            name="amino_cap_%d" % j,
        )

    # Exactly the required number of total assignments
    model.addConstr(
        gp.quicksum(
            x[i, j]
            for i in range(peak_count)
            for j in range(amino_acid_count)
        )
        == required_assignments,
        name="total_assignments",
    )

    # NOE restrictions: forbid simultaneous assignment of paired (peak, amino) combos
    for idx, pair in enumerate(noe_pairs):
        pa, aa, pb, ab = pair
        model.addConstr(
            x[pa, aa] + x[pb, ab] <= 1,
            name="noe_%d" % idx,
        )

    model.optimize()

    if model.status == GRB.Status.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status in (GRB.Status.INFEASIBLE, GRB.Status.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": "failed_status_%d" % model.status}
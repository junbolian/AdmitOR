import gurobipy as gp
from gurobipy import GRB
import re


def solve(params):
    peak_count = params["peak_count"]
    amino_acid_count = params["amino_acid_count"]
    noe_rhs_1 = params["noe_rhs_peak1_aa1_peak2_aa0"]
    noe_rhs_2 = params["noe_rhs_peak1_aa3_peak2_aa0"]
    num_assignments = params["num_assignments"]

    P = range(peak_count)
    A = range(amino_acid_count)

    # Try to get cost matrix directly from various possible keys
    assignment_cost = None
    for mat_key in ("assignment_cost", "cost", "costs", "cost_matrix", "assignment_costs"):
        if mat_key in params:
            raw = params[mat_key]
            if isinstance(raw, dict):
                cost = [[None] * amino_acid_count for _ in range(peak_count)]
                for k, v in raw.items():
                    if isinstance(k, tuple) and len(k) == 2:
                        p, a = int(k[0]), int(k[1])
                    elif isinstance(k, str):
                        m = re.match(r'.*peak(\d+).*aa(\d+)', k)
                        if m:
                            p, a = int(m.group(1)), int(m.group(2))
                        else:
                            continue
                    else:
                        continue
                    if 0 <= p < peak_count and 0 <= a < amino_acid_count:
                        cost[p][a] = float(v)
                assignment_cost = cost
            else:
                assignment_cost = raw
            break

    if assignment_cost is None:
        # Construct from individual entries scattered in params
        cost = [[None] * amino_acid_count for _ in range(peak_count)]
        for key, val in params.items():
            if not isinstance(val, (int, float)):
                continue
            if key.startswith("noe_rhs"):
                continue
            # Match pattern: ..._peak{p}_aa{a} at end of key
            m = re.match(r'.*_peak(\d+)_aa(\d+)$', key)
            if m:
                p, a = int(m.group(1)), int(m.group(2))
                if 0 <= p < peak_count and 0 <= a < amino_acid_count:
                    cost[p][a] = float(val)
        assignment_cost = cost

    # Fill None entries with row max (conservative for minimization)
    for p in range(peak_count):
        row = assignment_cost[p]
        known_vals = [row[a] for a in range(amino_acid_count) if row[a] is not None]
        if known_vals:
            rmax = max(known_vals)
            for a in range(amino_acid_count):
                if row[a] is None:
                    row[a] = rmax
        else:
            for a in range(amino_acid_count):
                row[a] = 0.0

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(P, A, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(assignment_cost[p][a] * x[p, a] for p in P for a in A),
        GRB.MINIMIZE
    )

    for p in P:
        model.addConstr(gp.quicksum(x[p, a] for a in A) <= 1, name=f"peak_{p}")

    for a in A:
        model.addConstr(gp.quicksum(x[p, a] for p in P) <= 1, name=f"aa_{a}")

    model.addConstr(
        gp.quicksum(x[p, a] for p in P for a in A) == num_assignments,
        name="total_assignments"
    )

    model.addConstr(x[1, 1] + x[2, 0] <= noe_rhs_1, name="noe_p1a1_p2a0")
    model.addConstr(x[1, 3] + x[2, 0] <= noe_rhs_2, name="noe_p1a3_p2a0")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}
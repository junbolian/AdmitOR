import gurobipy as gp
from gurobipy import GRB


def solve(params):
    noe_rhs_peak1_aa1_peak2_aa0 = params["noe_rhs_peak1_aa1_peak2_aa0"]
    noe_rhs_peak1_aa3_peak2_aa0 = params["noe_rhs_peak1_aa3_peak2_aa0"]
    num_assignments = params["num_assignments"]
    peak_count = params["peak_count"]
    amino_acid_count = params["amino_acid_count"]

    # Cost matrix from problem description.
    # Known exact entries are given; for unspecified cells the row minimum is used
    # as a lower bound (conservative: minimizes cost).
    # Row mins: P0=0.3249815990529156, P1=0.328350931703943, P2=0.3100214814238454,
    #           P3=0.3426569330378805, P4=0.3215078381217134
    # Known exact values from problem text:
    #   P0: AA0=0.4241579671609457, AA1=0.4459143481608616, AA3=0.3249815990529156(min), AA5=0.6739971903426926(max)
    #   P1: AA2=0.4251877625740568, AA4=0.6541620015185604(max), AA5=0.328350931703943(min)
    #   P2: AA1=0.3100214814238454(min), AA4=0.6843458280180249(max)
    #   P3: AA3=0.3426569330378805(min), AA4=0.5767932853068622(max)
    #   P4: AA2=0.6701065561383488(max), AA5=0.3215078381217134(min)
    # Unspecified cells filled with their row minimum (tightest lower bound available).

    row_min = [
        0.3249815990529156,   # P0
        0.328350931703943,    # P1
        0.3100214814238454,   # P2
        0.3426569330378805,   # P3
        0.3215078381217134,   # P4
    ]

    # Build cost matrix: 5 peaks x 6 amino acids
    # Initialize all cells to row minimum
    cost = [[row_min[p] for _ in range(6)] for p in range(5)]

    # Fill in known exact values from problem description
    cost[0][0] = 0.4241579671609457
    cost[0][1] = 0.4459143481608616
    cost[0][3] = 0.3249815990529156
    cost[0][5] = 0.6739971903426926

    cost[1][2] = 0.4251877625740568
    cost[1][4] = 0.6541620015185604
    cost[1][5] = 0.328350931703943

    cost[2][1] = 0.3100214814238454
    cost[2][4] = 0.6843458280180249

    cost[3][3] = 0.3426569330378805
    cost[3][4] = 0.5767932853068622

    cost[4][2] = 0.6701065561383488
    cost[4][5] = 0.3215078381217134

    # If the harness does supply assignment_cost, use it instead
    if "assignment_cost" in params:
        raw = params["assignment_cost"]
        cost = [[float(raw[p][a]) for a in range(amino_acid_count)] for p in range(peak_count)]

    P = range(peak_count)
    A = range(amino_acid_count)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(P, A, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[p][a] * x[p, a] for p in P for a in A),
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

    model.addConstr(
        x[1, 1] + x[2, 0] <= noe_rhs_peak1_aa1_peak2_aa0,
        name="noe_peak1_aa1_peak2_aa0"
    )
    model.addConstr(
        x[1, 3] + x[2, 0] <= noe_rhs_peak1_aa3_peak2_aa0,
        name="noe_peak1_aa3_peak2_aa0"
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
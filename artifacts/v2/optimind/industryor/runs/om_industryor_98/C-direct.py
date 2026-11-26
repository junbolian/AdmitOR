import gurobipy as gp
from gurobipy import GRB

def solve(params):
    bw = {
        ('A','B'): params["bw_A_B"],
        ('A','C'): params["bw_A_C"],
        ('A','E'): params["bw_A_E"],
        ('B','A'): params["bw_B_A"],
        ('B','C'): params["bw_B_C"],
        ('B','D'): params["bw_B_D"],
        ('B','E'): params["bw_B_E"],
        ('C','A'): params["bw_C_A"],
        ('C','D'): params["bw_C_D"],
        ('C','E'): params["bw_C_E"],
        ('D','A'): params["bw_D_A"],
        ('D','B'): params["bw_D_B"],
        ('D','C'): params["bw_D_C"],
        ('D','E'): params["bw_D_E"],
        ('E','B'): params["bw_E_B"],
        ('E','D'): params["bw_E_D"],
    }
    zero_bw = params["zero_bandwidth"]

    # Only keep arcs with positive bandwidth
    arcs = [(i, j) for (i, j), w in bw.items() if w > zero_bw]
    nodes = ['A', 'B', 'C', 'D', 'E']

    # We need a path from A to E that passes through C (no loops).
    # Strategy: find path A->...->C->...->E maximizing min-bandwidth.
    # We decompose into two sub-paths: A->C and C->E, each loop-free,
    # with no shared intermediate nodes (to avoid loops in the full path).
    #
    # For each sub-path we use a flow-based formulation with a bottleneck variable.
    # We enumerate all pairs of node-disjoint sub-path sets or handle via MILP.
    #
    # Full MILP formulation:
    # - x[i,j] in {0,1}: arc used in segment A->C
    # - y[i,j] in {0,1}: arc used in segment C->E
    # - z[i] in {0,1}: node i is used in segment A->C (intermediate, not A or C)
    # - w[i] in {0,1}: node i is used in segment C->E (intermediate, not C or E)
    # - node disjointness: z[i] + w[i] <= 1 for intermediate nodes B, D
    # - bottleneck: T = min bandwidth on the combined path
    #
    # For the bottleneck: T <= bw[i,j] * (x[i,j] + y[i,j]) + M*(1 - x[i,j] - y[i,j])
    # i.e., if arc is used, T <= bw[i,j].

    M_big = max(bw.values()) + 1

    model = gp.Model("max_bandwidth_path_through_C")
    model.setParam("OutputFlag", 0)

    # Arc usage variables
    x = {}  # A -> C segment
    y_var = {}  # C -> E segment
    for (i, j) in arcs:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
        y_var[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    # Node usage for intermediate nodes in each segment
    # intermediate nodes for A->C: B, D (not A or C)
    # intermediate nodes for C->E: A, B, D (not C or E)
    # But A is the source of segment 1 and must not appear as intermediate in segment 2
    # E is the sink of segment 2 and must not appear as intermediate in segment 1
    # We track node usage to enforce no-loop and node-disjointness

    # Node visit indicators (intermediate usage)
    # For segment x (A->C): node v is intermediate if v not in {A, C}
    # For segment y (C->E): node v is intermediate if v not in {C, E}
    # Also A should not appear in segment y, E should not appear in segment x
    # to avoid loops across the full path.

    nv_x = {}  # node v visited in segment x (intermediate: B, D, E excluded as sink not reachable sensibly)
    nv_y = {}  # node v visited in segment y (intermediate: A, B, D)

    seg_x_intermediates = ['B', 'D']  # E could appear but we'll exclude it via flow
    seg_y_intermediates = ['A', 'B', 'D']  # A could appear but we'll exclude it via flow

    for v in nodes:
        nv_x[v] = model.addVar(vtype=GRB.BINARY, name=f"nx_{v}")
        nv_y[v] = model.addVar(vtype=GRB.BINARY, name=f"ny_{v}")

    # Bottleneck variable
    T = model.addVar(lb=0.0, name="T")

    model.setObjective(T, GRB.MAXIMIZE)

    # Flow conservation for segment x (source=A, sink=C)
    for v in nodes:
        out_x = gp.quicksum(x[i, j] for (i, j) in arcs if i == v)
        in_x  = gp.quicksum(x[i, j] for (i, j) in arcs if j == v)
        if v == 'A':
            model.addConstr(out_x - in_x == 1, name=f"flow_x_{v}")
        elif v == 'C':
            model.addConstr(out_x - in_x == -1, name=f"flow_x_{v}")
        else:
            model.addConstr(out_x - in_x == 0, name=f"flow_x_{v}")

    # Flow conservation for segment y (source=C, sink=E)
    for v in nodes:
        out_y = gp.quicksum(y_var[i, j] for (i, j) in arcs if i == v)
        in_y  = gp.quicksum(y_var[i, j] for (i, j) in arcs if j == v)
        if v == 'C':
            model.addConstr(out_y - in_y == 1, name=f"flow_y_{v}")
        elif v == 'E':
            model.addConstr(out_y - in_y == -1, name=f"flow_y_{v}")
        else:
            model.addConstr(out_y - in_y == 0, name=f"flow_y_{v}")

    # Link node visit indicators to arc usage
    for v in nodes:
        # nv_x[v] = 1 if v is visited (has incoming arc) in segment x, except source A
        in_arcs_x = [x[i, j] for (i, j) in arcs if j == v]
        out_arcs_x = [x[i, j] for (i, j) in arcs if i == v]
        if in_arcs_x:
            model.addConstr(nv_x[v] >= gp.quicksum(in_arcs_x) / len(in_arcs_x),
                            name=f"nv_x_lb_{v}")
            model.addConstr(nv_x[v] <= gp.quicksum(in_arcs_x), name=f"nv_x_ub_{v}")
        else:
            model.addConstr(nv_x[v] == 0)

        in_arcs_y = [y_var[i, j] for (i, j) in arcs if j == v]
        if in_arcs_y:
            model.addConstr(nv_y[v] >= gp.quicksum(in_arcs_y) / len(in_arcs_y),
                            name=f"nv_y_lb_{v}")
            model.addConstr(nv_y[v] <= gp.quicksum(in_arcs_y), name=f"nv_y_ub_{v}")
        else:
            model.addConstr(nv_y[v] == 0)

    # No loops: E must not appear in segment x (would create A->E->...->C->...->E loop)
    model.addConstr(nv_x['E'] == 0, name="no_E_in_seg_x")
    # No loops: A must not appear as destination in segment y
    model.addConstr(nv_y['A'] == 0, name="no_A_in_seg_y")

    # Node disjointness for intermediate nodes B and D
    # (A is source of x, C is junction, E is sink of y — they appear exactly once)
    for v in ['B', 'D']:
        model.addConstr(nv_x[v] + nv_y[v] <= 1, name=f"node_disj_{v}")

    # Bottleneck constraints: T <= bw[i,j] if arc (i,j) is used in either segment
    for (i, j) in arcs:
        w_ij = bw[i, j]
        # If x[i,j] = 1: T <= w_ij  =>  T <= w_ij + M*(1 - x[i,j])
        model.addConstr(T <= w_ij + M_big * (1 - x[i, j]), name=f"btn_x_{i}_{j}")
        # If y[i,j] = 1: T <= w_ij  =>  T <= w_ij + M*(1 - y[i,j])
        model.addConstr(T <= w_ij + M_big * (1 - y_var[i, j]), name=f"btn_y_{i}_{j}")

    # At least one arc must be used in each segment (path must exist)
    model.addConstr(gp.quicksum(x[i, j] for (i, j) in arcs) >= 1, name="seg_x_nonempty")
    model.addConstr(gp.quicksum(y_var[i, j] for (i, j) in arcs) >= 1, name="seg_y_nonempty")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
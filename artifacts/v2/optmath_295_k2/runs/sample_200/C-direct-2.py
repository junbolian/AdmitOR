import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pt_j0_o0 = params["processing_time_j0_o0"]
    pt_j0_o1 = params["processing_time_j0_o1"]
    pt_j1_o0 = params["processing_time_j1_o0"]
    pt_j1_o1 = params["processing_time_j1_o1"]
    pt_j2_o0 = params["processing_time_j2_o0"]
    pt_j2_o1 = params["processing_time_j2_o1"]
    lag_j0 = params["precedence_lag_j0"]
    lag_j1 = params["precedence_lag_j1"]
    lag_j2 = params["precedence_lag_j2"]
    bigM = params["machine_disjunctive_bigM"]

    model = gp.Model("job_shop")
    model.setParam("OutputFlag", 0)

    # Start time variables for each operation
    s_j0_o0 = model.addVar(lb=0.0, name="s_j0_o0")
    s_j0_o1 = model.addVar(lb=0.0, name="s_j0_o1")
    s_j1_o0 = model.addVar(lb=0.0, name="s_j1_o0")
    s_j1_o1 = model.addVar(lb=0.0, name="s_j1_o1")
    s_j2_o0 = model.addVar(lb=0.0, name="s_j2_o0")
    s_j2_o1 = model.addVar(lb=0.0, name="s_j2_o1")

    # Makespan variable
    cmax = model.addVar(lb=0.0, name="cmax")

    # Binary disjunctive variables for machine capacity constraints
    # Based on the problem description, pairs that share a machine:
    # (j0_o0, j0_o1), (j0_o0, j1_o0), and by extension all pairs on same machine
    # The problem mentions specific pairs; we'll cover all pairs between operations
    # on the same machine using binary variables.
    # From the problem description the explicit pairs mentioned are:
    # - j0_o0 vs j0_o1 (same machine)
    # - j0_o0 vs j1_o0 (same machine)
    # We infer machine assignments: machine 0 handles j0_o0, j1_o0, j2_o0
    # and machine 1 handles j0_o1, j1_o1, j2_o1 (typical job shop pattern)

    # Disjunctive binaries: y_AB = 1 means A starts before B
    y_j0o0_j0o1 = model.addVar(vtype=GRB.BINARY, name="y_j0o0_j0o1")
    y_j0o0_j1o0 = model.addVar(vtype=GRB.BINARY, name="y_j0o0_j1o0")
    y_j0o0_j2o0 = model.addVar(vtype=GRB.BINARY, name="y_j0o0_j2o0")
    y_j1o0_j2o0 = model.addVar(vtype=GRB.BINARY, name="y_j1o0_j2o0")
    y_j0o1_j1o1 = model.addVar(vtype=GRB.BINARY, name="y_j0o1_j1o1")
    y_j0o1_j2o1 = model.addVar(vtype=GRB.BINARY, name="y_j0o1_j2o1")
    y_j1o1_j2o1 = model.addVar(vtype=GRB.BINARY, name="y_j1o1_j2o1")

    model.update()

    # Precedence constraints
    model.addConstr(s_j0_o1 >= s_j0_o0 + pt_j0_o0 + lag_j0, name="prec_j0")
    model.addConstr(s_j1_o1 >= s_j1_o0 + pt_j1_o0 + lag_j1, name="prec_j1")
    model.addConstr(s_j2_o1 >= s_j2_o0 + pt_j2_o0 + lag_j2, name="prec_j2")

    # Machine capacity constraints (disjunctive)
    # Machine 0: j0_o0, j1_o0, j2_o0
    # j0_o0 vs j1_o0
    model.addConstr(s_j1_o0 >= s_j0_o0 + pt_j0_o0 - bigM * (1 - y_j0o0_j1o0), name="mc_j0o0_j1o0_a")
    model.addConstr(s_j0_o0 >= s_j1_o0 + pt_j1_o0 - bigM * y_j0o0_j1o0, name="mc_j0o0_j1o0_b")

    # j0_o0 vs j2_o0
    model.addConstr(s_j2_o0 >= s_j0_o0 + pt_j0_o0 - bigM * (1 - y_j0o0_j2o0), name="mc_j0o0_j2o0_a")
    model.addConstr(s_j0_o0 >= s_j2_o0 + pt_j2_o0 - bigM * y_j0o0_j2o0, name="mc_j0o0_j2o0_b")

    # j1_o0 vs j2_o0
    model.addConstr(s_j2_o0 >= s_j1_o0 + pt_j1_o0 - bigM * (1 - y_j1o0_j2o0), name="mc_j1o0_j2o0_a")
    model.addConstr(s_j1_o0 >= s_j2_o0 + pt_j2_o0 - bigM * y_j1o0_j2o0, name="mc_j1o0_j2o0_b")

    # j0_o0 vs j0_o1 (from problem description - they share a machine)
    model.addConstr(s_j0_o1 >= s_j0_o0 + pt_j0_o0 - bigM * (1 - y_j0o0_j0o1), name="mc_j0o0_j0o1_a")
    model.addConstr(s_j0_o0 >= s_j0_o1 + pt_j0_o1 - bigM * y_j0o0_j0o1, name="mc_j0o0_j0o1_b")

    # Machine 1: j0_o1, j1_o1, j2_o1
    # j0_o1 vs j1_o1
    model.addConstr(s_j1_o1 >= s_j0_o1 + pt_j0_o1 - bigM * (1 - y_j0o1_j1o1), name="mc_j0o1_j1o1_a")
    model.addConstr(s_j0_o1 >= s_j1_o1 + pt_j1_o1 - bigM * y_j0o1_j1o1, name="mc_j0o1_j1o1_b")

    # j0_o1 vs j2_o1
    model.addConstr(s_j2_o1 >= s_j0_o1 + pt_j0_o1 - bigM * (1 - y_j0o1_j2o1), name="mc_j0o1_j2o1_a")
    model.addConstr(s_j0_o1 >= s_j2_o1 + pt_j2_o1 - bigM * y_j0o1_j2o1, name="mc_j0o1_j2o1_b")

    # j1_o1 vs j2_o1
    model.addConstr(s_j2_o1 >= s_j1_o1 + pt_j1_o1 - bigM * (1 - y_j1o1_j2o1), name="mc_j1o1_j2o1_a")
    model.addConstr(s_j1_o1 >= s_j2_o1 + pt_j2_o1 - bigM * y_j1o1_j2o1, name="mc_j1o1_j2o1_b")

    # Makespan constraints
    model.addConstr(cmax >= s_j0_o0 + pt_j0_o0, name="ms_j0_o0")
    model.addConstr(cmax >= s_j0_o1 + pt_j0_o1, name="ms_j0_o1")
    model.addConstr(cmax >= s_j1_o0 + pt_j1_o0, name="ms_j1_o0")
    model.addConstr(cmax >= s_j1_o1 + pt_j1_o1, name="ms_j1_o1")
    model.addConstr(cmax >= s_j2_o0 + pt_j2_o0, name="ms_j2_o0")
    model.addConstr(cmax >= s_j2_o1 + pt_j2_o1, name="ms_j2_o1")

    # Objective
    model.setObjective(cmax, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
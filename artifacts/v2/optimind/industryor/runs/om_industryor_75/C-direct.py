import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_A = params["processing_cost_A"]  # list of 10 values
    cost_B = params["processing_cost_B"]  # list of 10 values
    cost_C = params["processing_cost_C"]  # list of 10 values
    setup_A = params["setup_cost_A"]
    setup_B = params["setup_cost_B"]
    setup_C = params["setup_cost_C"]
    max_on_C = params["max_parts_on_C"]

    n_parts = 10
    parts = range(n_parts)  # 0-indexed: part i corresponds to part (i+1) in problem

    model = gp.Model("machine_assignment")
    model.setParam("OutputFlag", 0)

    # x[i, m] = 1 if part i is assigned to machine m (0=A, 1=B, 2=C)
    x = model.addVars(n_parts, 3, vtype=GRB.BINARY, name="x")

    # y[m] = 1 if machine m is used (setup cost incurred)
    y = model.addVars(3, vtype=GRB.BINARY, name="y")

    # Each part must be assigned to exactly one machine
    for i in parts:
        model.addConstr(x[i, 0] + x[i, 1] + x[i, 2] == 1, name=f"assign_{i}")

    # Setup cost linking: if any part is on machine m, y[m] = 1
    for i in parts:
        for mc in range(3):
            model.addConstr(x[i, mc] <= y[mc], name=f"setup_link_{i}_{mc}")

    # Constraint 2: part 1 (index 0) on A => part 2 (index 1) on B or C (not A)
    #               part 1 on B or C => part 2 on A
    # Equivalently: x[0,0] = 1 - x[1,0]  =>  x[0,0] + x[1,0] = 1
    # (part1 on A XOR part2 on A, one of them must be on A and not both)
    model.addConstr(x[0, 0] + x[1, 0] == 1, name="constraint2")

    # Constraint 3: part 3 (index 2) on A, part 4 (index 3) on B, part 5 (index 4) on C
    model.addConstr(x[2, 0] == 1, name="part3_on_A")
    model.addConstr(x[3, 1] == 1, name="part4_on_B")
    model.addConstr(x[4, 2] == 1, name="part5_on_C")

    # Constraint 4: number of parts on C <= max_parts_on_C
    model.addConstr(gp.quicksum(x[i, 2] for i in parts) <= max_on_C, name="max_C")

    # Objective: minimize total processing cost + setup costs
    processing = gp.quicksum(
        cost_A[i] * x[i, 0] + cost_B[i] * x[i, 1] + cost_C[i] * x[i, 2]
        for i in parts
    )
    setup = setup_A * y[0] + setup_B * y[1] + setup_C * y[2]

    model.setObjective(processing + setup, GRB.MINIMIZE)

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
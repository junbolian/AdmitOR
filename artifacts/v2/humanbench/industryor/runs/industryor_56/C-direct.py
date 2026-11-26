import gurobipy as gp
from gurobipy import GRB

def solve(params):
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    setup_cost_C = params["setup_cost_C"]
    proc_A = params["processing_cost_A"]  # list of 10 values, index 0..9 for parts 1..10
    proc_B = params["processing_cost_B"]
    proc_C = params["processing_cost_C"]
    max_parts_C = params["max_parts_on_C"]

    n_parts = 10
    parts = range(n_parts)  # 0-indexed: part i corresponds to part (i+1)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,e]: 1 if part i+1 is processed on equipment e (0=A, 1=B, 2=C)
    x = model.addVars(n_parts, 3, vtype=GRB.BINARY, name="x")

    # y[e]: 1 if equipment e is used at all (setup incurred)
    y = model.addVars(3, vtype=GRB.BINARY, name="y")

    # Each part processed on exactly one equipment
    for i in parts:
        model.addConstr(x[i, 0] + x[i, 1] + x[i, 2] == 1, name=f"assign_{i}")

    # Constraint (2): part 1 (index 0) and part 2 (index 1) must be on different "sides"
    # If part1 on A => part2 on B or C (not A)
    # If part1 on B or C => part2 on A
    # Equivalently: x[0,0] + x[1,0] == 1 (exactly one of them is on A)
    model.addConstr(x[0, 0] + x[1, 0] == 1, name="constraint2")

    # Constraint (3): part 3 on A, part 4 on B, part 5 on C (0-indexed: parts 2,3,4)
    model.addConstr(x[2, 0] == 1, name="part3_A")
    model.addConstr(x[3, 1] == 1, name="part4_B")
    model.addConstr(x[4, 2] == 1, name="part5_C")

    # Constraint (4): number of parts on C <= max_parts_C
    model.addConstr(gp.quicksum(x[i, 2] for i in parts) <= max_parts_C, name="max_C")

    # Link y[e] to x: y[e] = 1 if any part is on equipment e
    for e in range(3):
        # y[e] >= x[i,e] for all i
        for i in parts:
            model.addConstr(y[e] >= x[i, e], name=f"setup_lb_{e}_{i}")
        # y[e] <= sum of x[i,e]
        model.addConstr(y[e] <= gp.quicksum(x[i, e] for i in parts), name=f"setup_ub_{e}")

    # Objective: minimize total cost
    setup_costs = [setup_cost_A, setup_cost_B, setup_cost_C]
    proc_costs = [proc_A, proc_B, proc_C]

    obj = gp.quicksum(setup_costs[e] * y[e] for e in range(3))
    obj += gp.quicksum(proc_costs[e][i] * x[i, e] for i in parts for e in range(3))

    model.setObjective(obj, GRB.MINIMIZE)

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
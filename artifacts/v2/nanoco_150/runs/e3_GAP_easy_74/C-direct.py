import gurobipy as gp
from gurobipy import GRB

def solve(params):
    labor_limit = [
        params["labor_limit_S1"],
        params["labor_limit_S2"],
        params["labor_limit_S3"],
    ]
    labor_req = params["labor_req"]   # 3 x 7 matrix
    bid_price = params["bid_price"]   # 3 x 7 matrix
    num_sub = params["num_subcontractors"]
    num_ph  = params["num_phases"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if subcontractor i is assigned to phase j
    x = model.addVars(num_sub, num_ph, vtype=GRB.BINARY, name="x")

    # Objective: minimize total bid price
    model.setObjective(
        gp.quicksum(bid_price[i][j] * x[i, j]
                    for i in range(num_sub)
                    for j in range(num_ph)),
        GRB.MINIMIZE,
    )

    # Each phase assigned to exactly one subcontractor
    for j in range(num_ph):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_sub)) == 1,
            name=f"assign_phase_{j}",
        )

    # Labor capacity constraints
    for i in range(num_sub):
        model.addConstr(
            gp.quicksum(labor_req[i][j] * x[i, j] for j in range(num_ph)) <= labor_limit[i],
            name=f"labor_limit_{i}",
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
        return {"objective": None, "status": f"gurobi_status_{status}"}
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    w = {
        (0,1): params["weights_01"],
        (0,2): params["weights_02"],
        (0,3): params["weights_03"],
        (1,0): params["weights_10"],
        (1,2): params["weights_12"],
        (1,3): params["weights_13"],
        (2,0): params["weights_20"],
        (2,1): params["weights_21"],
        (2,3): params["weights_23"],
        (3,0): params["weights_30"],
        (3,1): params["weights_31"],
        (3,2): params["weights_32"],
    }
    k = params["facilities_to_select"]
    nodes = [0, 1, 2, 3]
    pairs = list(w.keys())

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    model.setObjective(gp.quicksum(w[p] * z[p] for p in pairs), GRB.MAXIMIZE)

    model.addConstr(gp.quicksum(x[i] for i in nodes) == k, name="facility_count")

    for (i, j) in pairs:
        model.addConstr(z[i, j] <= x[i], name=f"zpair_i_{i}_{j}")
        model.addConstr(z[i, j] <= x[j], name=f"zpair_j_{i}_{j}")
        model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"zpair_lb_{i}_{j}")

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
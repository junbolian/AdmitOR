import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_slots = params["n_slots"]
    edges = params["edges"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable for each edge: 1 if selected in matching
    x = model.addVars(len(edges), vtype=GRB.BINARY, name="x")

    # Objective: maximize number of selected edges
    model.setObjective(gp.quicksum(x[i] for i in range(len(edges))), GRB.MAXIMIZE)

    # Each slot participates in at most one selected edge
    for slot in range(n_slots):
        incident = [i for i, (u, v) in enumerate(edges) if u == slot or v == slot]
        if incident:
            model.addConstr(gp.quicksum(x[i] for i in incident) <= 1)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
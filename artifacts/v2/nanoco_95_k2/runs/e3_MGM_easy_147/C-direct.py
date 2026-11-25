import gurobipy as gp
from gurobipy import GRB


def solve(params):
    edges = params["edges"]
    num_nodes = params["num_nodes"]

    model = gp.Model("max_cardinality_matching")
    model.Params.OutputFlag = 0

    # x[i] = 1 if edge i is selected in the matching, 0 otherwise
    x = model.addVars(len(edges), vtype=GRB.BINARY, name="x")

    # Maximize the number of selected edges
    model.setObjective(gp.quicksum(x[i] for i in range(len(edges))), GRB.MAXIMIZE)

    # Each node may be incident to at most one selected edge
    for v in range(num_nodes):
        incident = []
        for i, (a, b) in enumerate(edges):
            if a == v or b == v:
                incident.append(x[i])
        if incident:
            model.addConstr(gp.quicksum(incident) <= 1, name=f"node_{v}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "no optimal solution"}
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edges = params["edges"]
    num_nodes = params["num_nodes"]

    # Normalize edges to tuples
    edge_list = [tuple(e) for e in edges]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable for each edge: 1 if selected in matching
    x = model.addVars(edge_list, vtype=GRB.BINARY, name="x")

    # Objective: maximize number of selected edges
    model.setObjective(gp.quicksum(x[e] for e in edge_list), GRB.MAXIMIZE)

    # Each node incident to at most one selected edge
    for node in range(num_nodes):
        incident = [e for e in edge_list if node in e]
        if incident:
            model.addConstr(gp.quicksum(x[e] for e in incident) <= 1, name=f"node_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
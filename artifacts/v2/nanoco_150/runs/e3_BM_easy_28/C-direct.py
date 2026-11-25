import gurobipy as gp
from gurobipy import GRB

def solve(params):
    link_weights = params["link_weights"]
    port_limits = params["port_limits"]

    # Fixed edge list (structural constants)
    edges = [
        (0,1),(0,3),(0,5),(0,6),(0,7),
        (1,2),(1,3),(1,4),(1,5),(1,6),
        (2,3),(2,4),(2,7),(3,4),(3,5),
        (4,5),(4,6),(4,7),(5,7),(6,7)
    ]
    num_edges = 20
    num_nodes = 8

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable for each link
    x = model.addVars(num_edges, vtype=GRB.BINARY, name="x")

    # Objective: maximize total bandwidth revenue
    model.setObjective(
        gp.quicksum(link_weights[i] * x[i] for i in range(num_edges)),
        GRB.MAXIMIZE
    )

    # Port density constraints: sum of selected links incident to each node <= port_limit
    for node in range(num_nodes):
        incident = [i for i, (u, v) in enumerate(edges) if u == node or v == node]
        model.addConstr(
            gp.quicksum(x[i] for i in incident) <= port_limits[node],
            name=f"port_{node}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
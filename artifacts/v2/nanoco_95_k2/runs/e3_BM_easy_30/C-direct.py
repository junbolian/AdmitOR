import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_weights = params["edge_weights"]
    cell_capacities = params["cell_capacities"]

    # Edge definitions (structural constants - fixed topology)
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 7),
        (1, 5), (1, 7),
        (2, 3), (2, 6), (2, 7), (2, 8),
        (3, 7),
        (4, 5), (4, 6),
        (5, 7), (5, 8)
    ]
    num_edges = len(edges)  # 16

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable for each edge: 1 if selected, 0 otherwise
    x = model.addVars(num_edges, vtype=GRB.BINARY, name="x")

    # Objective: maximize total task execution value
    model.setObjective(
        gp.quicksum(edge_weights[i] * x[i] for i in range(num_edges)),
        GRB.MAXIMIZE
    )

    # Capacity constraints: for each cell, sum of incident selected edges <= capacity
    for c in range(9):
        incident = [i for i, (u, v) in enumerate(edges) if u == c or v == c]
        if incident:
            model.addConstr(
                gp.quicksum(x[i] for i in incident) <= cell_capacities[c],
                name=f"cap_{c}"
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
        return {"objective": None, "status": f"solver_status_{status}"}
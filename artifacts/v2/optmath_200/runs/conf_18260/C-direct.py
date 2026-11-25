import gurobipy as gp
from gurobipy import GRB

def solve(params):
    service_costs = params["service_costs"]

    # Coverage sets: requirement index -> list of service indices (0-based)
    coverage = [
        [1, 2, 3, 4, 5, 6, 9, 10, 11, 16, 18, 19],       # Req 1
        [3, 5, 6, 8, 9, 10, 11, 13, 14, 16, 18],           # Req 2
        [0, 2, 5, 6, 8, 9, 10, 11, 12, 13, 14, 18, 20, 21],# Req 3
        [0, 1, 2, 4, 5, 6, 9, 11, 12, 13, 14, 16, 17, 20], # Req 4
        [0, 1, 2, 3, 4, 6, 7, 8, 10, 12, 14, 16, 17, 18, 20],# Req 5
        [0, 2, 4, 6, 7, 8, 10, 11, 13, 14, 15, 16, 17, 19, 20],# Req 6
        [0, 1, 2, 5, 8, 10, 11, 12, 13, 20],               # Req 7
        [1, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 16, 19, 20],# Req 8
        [1, 2, 4, 5, 6, 8, 9, 11, 12, 13, 15, 17, 19, 20, 21],# Req 9
        [4, 5, 7, 9, 10, 11, 12, 13, 15],                  # Req 10
        [1, 2, 3, 4, 8, 9, 11, 14, 15, 17, 18, 20],        # Req 11
        [3, 4, 8, 9, 11, 12, 13, 14, 15, 18],              # Req 12
        [0, 1, 2, 3, 7, 10, 11, 13, 14, 16, 17, 19],       # Req 13
        [0, 1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14, 16, 17, 18, 19],# Req 14
        [1, 2, 3, 5, 6, 7, 8, 10, 12, 13, 14, 15, 17, 18, 19, 20, 21],# Req 15
        [0, 1, 2, 10, 11, 12, 14, 15, 17, 19, 21],         # Req 16
        [1, 4, 7, 8, 12, 13, 14, 15, 16, 18, 20],          # Req 17
        [2, 4, 5, 7, 11, 15, 16, 17, 18, 19],              # Req 18
        [0, 3, 4, 5, 8, 11, 13, 16, 17, 18, 19, 20, 21],   # Req 19
        [0, 1, 2, 3, 6, 7, 12, 13, 14, 15, 16, 17, 19],    # Req 20
        [0, 2, 3, 7, 11, 12, 15, 16, 17, 18, 20, 21],      # Req 21
        [0, 3, 5, 7, 9, 10, 11, 12, 13, 16, 17, 19, 21],   # Req 22
        [0, 2, 3, 8, 9, 13, 14, 15, 16, 19, 20],           # Req 23
        [0, 1, 2, 3, 4, 5, 9, 10, 12, 13, 14, 15, 16],     # Req 24
        [5, 6, 7, 9, 10, 11, 12, 14, 16, 17, 18, 19, 21],  # Req 25
        [1, 3, 6, 7, 9, 10, 11, 15, 16, 17, 18, 19, 20, 21],# Req 26
        [0, 1, 2, 3, 4, 5, 8, 10, 13, 14, 15, 17, 18, 19, 20, 21],# Req 27
        [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19],# Req 28
        [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 13, 14, 16, 17, 18, 19, 20, 21],# Req 29
        [0, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16, 20, 21],  # Req 30
        [0, 1, 3, 4, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 21],# Req 31
        [1, 3, 5, 8, 9, 10, 13, 14, 15, 18, 20, 21],       # Req 32
        [1, 5, 7, 10, 13, 14, 15, 16, 17, 19, 20],         # Req 33
        [0, 2, 3, 5, 7, 10, 11, 13, 14, 17, 18, 19],       # Req 34
        [0, 2, 3, 4, 5, 6, 7, 9, 11, 13, 14, 16, 17, 18, 19, 21],# Req 35
        [0, 2, 3, 6, 7, 8, 10, 14, 15, 18, 19, 20, 21],    # Req 36
    ]

    num_services = 22
    num_requirements = 36

    model = gp.Model("healthcare_set_cover")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: activate[j] = 1 if service j is activated
    activate = model.addVars(num_services, vtype=GRB.BINARY, name="activate")

    # Objective: minimize total activation cost
    model.setObjective(
        gp.quicksum(service_costs[j] * activate[j] for j in range(num_services)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each requirement must be covered by at least one active service
    for i in range(num_requirements):
        model.addConstr(
            gp.quicksum(activate[j] for j in coverage[i]) >= 1,
            name=f"req_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}
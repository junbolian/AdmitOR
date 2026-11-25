import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    N = 8

    required_edges = [(0, 2), (0, 6), (1, 3), (1, 6), (2, 4), (2, 7), (3, 5), (3, 7)]

    model = gp.Model("street_sweeping")
    model.Params.OutputFlag = 0

    # x[i, j] = number of times the vehicle traverses arc i -> j
    x = {}
    for i in range(N):
        for j in range(N):
            if i != j:
                x[i, j] = model.addVar(
                    vtype=GRB.INTEGER, lb=0, ub=10,
                    obj=distance_matrix[i][j],
                    name=f"x_{i}_{j}"
                )

    model.modelSense = GRB.MINIMIZE

    # Constraint 1: each required segment must be traversed at least once
    for (i, j) in required_edges:
        model.addConstr(x[i, j] + x[j, i] >= 1, name=f"req_{i}_{j}")

    # Constraint 2: flow balance (entries == exits) at every intersection
    for i in range(N):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(N) if j != i) ==
            gp.quicksum(x[j, i] for j in range(N) if j != i),
            name=f"flow_{i}"
        )

    # Constraint 3: connectivity — every non-empty subset of {1,…,7}
    # must have at least one arc leaving toward the depot side
    non_depot = list(range(1, N))
    for r in range(1, len(non_depot) + 1):
        for S in combinations(non_depot, r):
            S_set = set(S)
            complement = set(range(N)) - S_set
            model.addConstr(
                gp.quicksum(
                    x[i, j] for i in S_set for j in complement if i != j
                ) >= 1,
                name=f"cut_{r}_{'_'.join(map(str, S))}"
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}
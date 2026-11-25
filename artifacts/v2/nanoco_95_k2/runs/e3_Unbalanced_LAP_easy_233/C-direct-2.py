import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]

    num_attorneys = 8
    num_documents = 4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if attorney i is assigned to document j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
          for j in range(num_documents)]
         for i in range(num_attorneys)]

    # Each document assigned to exactly one attorney
    for j in range(num_documents):
        model.addConstr(gp.quicksum(x[i][j] for i in range(num_attorneys)) == 1)

    # Each attorney handles at most one document
    for i in range(num_attorneys):
        model.addConstr(gp.quicksum(x[i][j] for j in range(num_documents)) <= 1)

    # Minimize total review complexity cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j]
                    for i in range(num_attorneys)
                    for j in range(num_documents)),
        GRB.MINIMIZE
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
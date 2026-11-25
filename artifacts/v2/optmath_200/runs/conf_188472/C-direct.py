import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]        # list of length 4
    demand = params["demand"]        # list of length 6
    upper_limit = params["upper_limit"]  # 4x6 matrix
    cost = params["cost"]            # 4x6 matrix

    num_persons = 4
    num_projects = 6

    model = gp.Model("project_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = contribution of person i to project j
    x = [[model.addVar(lb=0.0, ub=upper_limit[i][j], name=f"x_{i}_{j}")
          for j in range(num_projects)]
         for i in range(num_persons)]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j]
                    for i in range(num_persons)
                    for j in range(num_projects)),
        GRB.MINIMIZE
    )

    # Person capacity constraints (equality)
    for i in range(num_persons):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_projects)) == supply[i],
            name=f"supply_{i}"
        )

    # Project demand constraints (equality)
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_persons)) == demand[j],
            name=f"demand_{j}"
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
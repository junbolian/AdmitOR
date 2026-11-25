import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]      # list of 7
    demand = params["demand"]          # list of 6
    cost = params["cost"]              # 7x6 matrix
    pair_capacity = params["pair_capacity"]  # 7x6 matrix

    num_persons = 7
    num_projects = 6
    persons = range(num_persons)
    projects = range(num_projects)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(persons, projects, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in persons for j in projects),
        GRB.MINIMIZE
    )

    # Individual capacity constraints
    for i in persons:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) <= capacity[i],
            name=f"cap_{i}"
        )

    # Project demand constraints
    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in persons) >= demand[j],
            name=f"demand_{j}"
        )

    # Pair capacity constraints
    for i in persons:
        for j in projects:
            model.addConstr(
                x[i, j] <= pair_capacity[i][j],
                name=f"pair_{i}_{j}"
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
        return {"objective": None, "status": f"gurobi_status_{status}"}
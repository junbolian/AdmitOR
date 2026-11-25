import gurobipy as gp
from gurobipy import GRB

def solve(params):
    activation_costs = params["activation_costs"]
    coverage_matrix = params["coverage_matrix"]

    num_areas = len(coverage_matrix)      # 34
    num_teams = len(activation_costs)     # 18

    model = gp.Model("emergency_coverage")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: activate team j or not
    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    # Objective: minimize total activation cost
    model.setObjective(
        gp.quicksum(activation_costs[j] * x[j] for j in range(num_teams)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each area must be covered by at least one capable team
    for i in range(num_areas):
        model.addConstr(
            gp.quicksum(coverage_matrix[i][j] * x[j] for j in range(num_teams)) >= 1,
            name=f"cover_area_{i}"
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
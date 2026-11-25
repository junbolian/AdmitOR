import gurobipy as gp
from gurobipy import GRB

def solve(params):
    employee_availability = params["employee_availability"]
    project_demand = params["project_demand"]
    assignment_cost = params["assignment_cost"]
    capacity = params["capacity"]

    num_employees = len(employee_availability)
    num_projects = len(project_demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units of time employee i assigns to project j
    x = [
        [
            model.addVar(lb=0.0, ub=capacity[i][j], name=f"x_{i}_{j}")
            for j in range(num_projects)
        ]
        for i in range(num_employees)
    ]

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i][j]
            for i in range(num_employees)
            for j in range(num_projects)
        ),
        GRB.MINIMIZE
    )

    # Employee availability constraints
    for i in range(num_employees):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_projects)) <= employee_availability[i],
            name=f"avail_{i}"
        )

    # Project demand constraints (exactly met)
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_employees)) == project_demand[j],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}
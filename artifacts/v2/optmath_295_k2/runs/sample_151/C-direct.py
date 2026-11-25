import gurobipy as gp
from gurobipy import GRB

def solve(params):
    member_time = params["member_time"]        # list of length 6
    project_effort = params["project_effort"]  # list of length 8
    assignment_cost = params["assignment_cost"]  # 6x8 matrix
    per_pair_capacity = params["per_pair_capacity"]  # 6x8 matrix

    num_persons = 6
    num_projects = 8

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = time person i spends on project j
    x = [
        [
            model.addVar(
                lb=0.0,
                ub=per_pair_capacity[i][j],
                name=f"x_{i}_{j}"
            )
            for j in range(num_projects)
        ]
        for i in range(num_persons)
    ]

    # Objective: minimize total assignment cost
    model.setObjective(
        gp.quicksum(
            assignment_cost[i][j] * x[i][j]
            for i in range(num_persons)
            for j in range(num_projects)
        ),
        GRB.MINIMIZE
    )

    # Each person's total time must equal their available time
    for i in range(num_persons):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_projects)) == member_time[i],
            name=f"member_time_{i}"
        )

    # Each project's total effort must equal its requirement
    for j in range(num_projects):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_persons)) == project_effort[j],
            name=f"project_effort_{j}"
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
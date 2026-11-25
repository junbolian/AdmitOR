import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    num_nodes = params["num_nodes"]
    num_customers = params["num_customers"]
    num_vehicles = params["num_vehicles"]

    nodes = list(range(num_nodes))
    customers = list(range(1, num_nodes))  # nodes 1..8
    depot = 0
    vehicles = list(range(num_vehicles))

    # Cost matrix
    c = {(i, j): distance_matrix[i][j] for i in nodes for j in nodes if i != j}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j,k] = 1 if vehicle k travels from i to j
    x = model.addVars(
        [(i, j, k) for i in nodes for j in nodes for k in vehicles if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # u[i,k]: position variable for MTZ subtour elimination (customers only)
    u = model.addVars(
        [(i, k) for i in customers for k in vehicles],
        lb=1.0, ub=float(num_customers),
        vtype=GRB.CONTINUOUS,
        name="u"
    )

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(c[i, j] * x[i, j, k] for (i, j, k) in x),
        GRB.MINIMIZE
    )

    # Each customer visited exactly once across all vehicles
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j, k] for i in nodes for k in vehicles if i != j) == 1,
            name=f"visit_{j}"
        )

    # Flow conservation for each vehicle at each customer
    for k in vehicles:
        for h in customers:
            model.addConstr(
                gp.quicksum(x[i, h, k] for i in nodes if i != h) ==
                gp.quicksum(x[h, j, k] for j in nodes if j != h),
                name=f"flow_{h}_{k}"
            )

    # Each vehicle departs depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[depot, j, k] for j in customers) == 1,
            name=f"depart_{k}"
        )

    # Each vehicle returns to depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[i, depot, k] for i in customers) == 1,
            name=f"return_{k}"
        )

    # MTZ subtour elimination
    for k in vehicles:
        for i in customers:
            for j in customers:
                if i != j:
                    model.addConstr(
                        u[i, k] - u[j, k] + num_customers * x[i, j, k] <= num_customers - 1,
                        name=f"mtz_{i}_{j}_{k}"
                    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}
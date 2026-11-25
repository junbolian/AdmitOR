import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_cost_matrix = params["shipping_cost_matrix"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_facilities = 4
    num_customers = 7
    facilities = range(num_facilities)
    customers = range(num_customers)

    # Normalize fixed_costs to list indexed by facility index
    if isinstance(fixed_costs, dict):
        fc = [fixed_costs[f"facility_{i}"] for i in facilities]
    else:
        fc = [fixed_costs[i] for i in facilities]

    # Normalize demands to list indexed by customer index
    if isinstance(demands, dict):
        dem = [demands[f"customer_{j}"] for j in customers]
    else:
        dem = [demands[j] for j in customers]

    # Normalize capacities to list indexed by facility index
    if isinstance(capacities, dict):
        cap = [capacities[f"facility_{i}"] for i in facilities]
    else:
        cap = [capacities[i] for i in facilities]

    # Normalize shipping cost matrix to 2D list [facility][customer]
    if isinstance(shipping_cost_matrix, dict):
        scm = []
        for i in facilities:
            row_key = f"facility_{i}"
            row = shipping_cost_matrix[row_key]
            if isinstance(row, dict):
                scm.append([row[f"customer_{j}"] for j in customers])
            else:
                scm.append([row[j] for j in customers])
    else:
        scm = []
        for i in facilities:
            row = shipping_cost_matrix[i]
            if isinstance(row, dict):
                scm.append([row[f"customer_{j}"] for j in customers])
            else:
                scm.append([row[j] for j in customers])

    model = gp.Model("distribution_center")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if facility i is opened
    y = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    # x[i,j] = units shipped from facility i to customer j
    x = model.addVars(facilities, customers, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fc[i] * y[i] for i in facilities) +
        gp.quicksum(scm[i][j] * x[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    # Demand fulfillment constraints
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j] for i in facilities) == dem[j],
            name=f"demand_{j}"
        )

    # Capacity and linking constraints
    for i in facilities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in customers) <= cap[i] * y[i],
            name=f"capacity_{i}"
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
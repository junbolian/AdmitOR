import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    dist = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]

    n_customers = 8
    nodes = list(range(9))          # 0 = depot, 1..8 = customers
    customers = list(range(1, 9))
    vehicles = list(range(num_vehicles))

    model = gp.Model()
    model.Params.OutputFlag = 0

    # x[k,i,j] = 1 if vehicle k travels arc (i,j)
    x = {}
    for k in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    x[k, i, j] = model.addVar(vtype=GRB.BINARY,
                                               name=f"x_{k}_{i}_{j}")

    # u[k,i] = position of node i in route of vehicle k (MTZ subtour elimination)
    u = {}
    for k in vehicles:
        for i in customers:
            u[k, i] = model.addVar(lb=1, ub=n_customers, vtype=GRB.CONTINUOUS,
                                   name=f"u_{k}_{i}")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[k, i, j]
                    for k in vehicles
                    for i in nodes
                    for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each customer visited exactly once across all vehicles
    for i in customers:
        model.addConstr(
            gp.quicksum(x[k, i, j] for k in vehicles for j in nodes if j != i) == 1,
            name=f"visit_{i}"
        )

    # Flow conservation at each customer for each vehicle
    for k in vehicles:
        for i in customers:
            model.addConstr(
                gp.quicksum(x[k, i, j] for j in nodes if j != i) ==
                gp.quicksum(x[k, j, i] for j in nodes if j != i),
                name=f"flow_{k}_{i}"
            )

    # Each vehicle departs depot at most once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[k, 0, j] for j in customers) <= 1,
            name=f"depart_{k}"
        )

    # Each vehicle returns to depot at most once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[k, j, 0] for j in customers) <= 1,
            name=f"return_{k}"
        )

    # If a vehicle visits any customer it must leave the depot
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[k, 0, j] for j in customers) ==
            gp.quicksum(x[k, j, 0] for j in customers),
            name=f"depot_balance_{k}"
        )

    # MTZ subtour elimination (only among customers)
    for k in vehicles:
        for i in customers:
            for j in customers:
                if i != j:
                    model.addConstr(
                        u[k, i] - u[k, j] + n_customers * x[k, i, j] <= n_customers - 1,
                        name=f"mtz_{k}_{i}_{j}"
                    )

    # Link u to x: if vehicle k travels i->j (customer->customer), u ordering enforced
    # (already handled by MTZ above)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}
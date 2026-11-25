import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]                          # 3 x 6
    production_cost = params["production_cost"]        # 3 x 6
    setup_cost = params["setup_cost"]                  # 3 x 6
    holding_cost = params["holding_cost"]              # 3
    capacity = params["capacity"]                      # 6
    capacity_consumption = params["capacity_consumption"]  # 3

    P = 3  # products
    T = 6  # months

    # Precompute cumulative demand from month t onward (used as big-M for production)
    # cum_demand_from[i][t] = sum of demand[i][t..T-1]
    cum_demand_from = []
    for i in range(P):
        row = []
        for t in range(T):
            row.append(sum(demand[i][s] for s in range(t, T)))
        cum_demand_from.append(row)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x[i, t]: production quantity of product i in month t
    x = model.addVars(P, T, lb=0.0, name="x")

    # y[i, t]: binary setup variable for product i in month t
    y = model.addVars(P, T, vtype=GRB.BINARY, name="y")

    # inv[i, t]: inventory of product i at end of month t
    inv = model.addVars(P, T, lb=0.0, name="inv")

    # Objective: minimize production + setup + holding costs
    obj = gp.quicksum(
        production_cost[i][t] * x[i, t]
        + setup_cost[i][t] * y[i, t]
        + holding_cost[i] * inv[i, t]
        for i in range(P) for t in range(T)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints (cumulative form):
    # sum_{s=0}^{t} x[i,s] - inv[i,t] = sum_{s=0}^{t} demand[i][s]
    # which means: inv[i,t] = sum_{s<=t} x[i,s] - sum_{s<=t} demand[i][s]
    # Equivalently: inv[i,t] = inv[i,t-1] + x[i,t] - demand[i][t]
    for i in range(P):
        for t in range(T):
            if t == 0:
                model.addConstr(
                    x[i, t] - inv[i, t] == demand[i][t],
                    name=f"inv_bal_{i}_{t}"
                )
            else:
                model.addConstr(
                    inv[i, t - 1] + x[i, t] - inv[i, t] == demand[i][t],
                    name=f"inv_bal_{i}_{t}"
                )

    # Setup constraints: production only if setup is active
    # x[i,t] <= cum_demand_from[i][t] * y[i,t]
    for i in range(P):
        for t in range(T):
            model.addConstr(
                x[i, t] <= cum_demand_from[i][t] * y[i, t],
                name=f"setup_{i}_{t}"
            )

    # Capacity constraints: sum over products of capacity_consumption[i] * x[i,t] <= capacity[t]
    for t in range(T):
        model.addConstr(
            gp.quicksum(capacity_consumption[i] * x[i, t] for i in range(P)) <= capacity[t],
            name=f"capacity_{t}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}
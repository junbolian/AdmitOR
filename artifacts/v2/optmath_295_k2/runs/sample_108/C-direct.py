import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]      # list/dict for P0, P1, P2
    demand = params["demand"]          # list/dict for C0, C1, C2, C3
    min_delivery = params["min_delivery"]  # list/dict for P0, P1, P2
    cost = params["cost"]              # 3x4 matrix, rows=producers, cols=contracts

    num_producers = 3
    num_contracts = 4
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model("energy_allocation")
    model.setParam("OutputFlag", 0)

    # x[i,j] = energy delivered by producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")

    # y[i,j] = 1 if producer i participates in contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: total output of each producer <= capacity
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"capacity_{i}"
        )

    # Demand constraints: total input to each contract >= demand
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= demand[j],
            name=f"demand_{j}"
        )

    # At least two producers must contribute to each contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= 2,
            name=f"min_contributors_{j}"
        )

    # Linking constraints: x[i,j] > 0 only if y[i,j] = 1
    # Use capacity[i] as big-M (producer can't deliver more than its total capacity)
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_upper_{i}_{j}"
            )

    # Minimum delivery threshold if producer participates
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_delivery_{i}_{j}"
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
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_cost = params["production_cost"]
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    min_delivery_per_producer = params["min_delivery_per_producer"]

    num_producers = 6
    num_contracts = 6
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model("energy_distribution")
    model.setParam("OutputFlag", 0)

    # x[i, j] = electricity from producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")

    # y[i, j] = 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(production_cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= producer_capacity[i],
            name=f"capacity_{i}"
        )

    # Contract demand constraints
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= contract_demand[j],
            name=f"demand_{j}"
        )

    # Minimum contributors per contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= min_contributors[j],
            name=f"min_contributors_{j}"
        )

    # Linking constraints: x[i,j] > 0 only if y[i,j] = 1
    # Also enforce minimum delivery if contributing
    for i in producers:
        for j in contracts:
            # If y[i,j] = 1, x[i,j] >= min_delivery_per_producer[i]
            # If y[i,j] = 0, x[i,j] = 0
            model.addConstr(
                x[i, j] >= min_delivery_per_producer[i] * y[i, j],
                name=f"min_delivery_{i}_{j}"
            )
            # Upper bound linking: x[i,j] <= capacity[i] * y[i,j]
            model.addConstr(
                x[i, j] <= producer_capacity[i] * y[i, j],
                name=f"upper_link_{i}_{j}"
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
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    production_cost = params["production_cost"]
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    min_delivery_per_producer = params["min_delivery_per_producer"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model("energy_distribution")
    model.Params.OutputFlag = 0

    # x[i,j] = electricity delivered by producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, vtype=GRB.CONTINUOUS, name="x")
    # y[i,j] = 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(production_cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE,
    )

    # Capacity limits: total generation by each producer across all contracts
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= producer_capacity[i],
            name=f"capacity_{i}",
        )

    # Contract fulfillment: total delivery to each contract meets minimum requirement
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= contract_demand[j],
            name=f"demand_{j}",
        )

    # Minimum contributors per contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= min_contributors[j],
            name=f"min_contributors_{j}",
        )

    # Minimum delivery per producer: if contributing, must deliver at least the minimum
    # x[i,j] >= min_delivery_per_producer[i] * y[i,j]
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i, j] >= min_delivery_per_producer[i] * y[i, j],
                name=f"min_delivery_{i}_{j}",
            )

    # Linking: x[i,j] > 0 implies y[i,j] = 1 (big-M upper bound)
    for i in producers:
        for j in contracts:
            M = min(producer_capacity[i], contract_demand[j])
            model.addConstr(
                x[i, j] <= M * y[i, j],
                name=f"link_{i}_{j}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": f"gurobi_status_{model.status}"}
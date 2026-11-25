import gurobipy as gp
from gurobipy import GRB

def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    min_delivery_per_producer = params["min_delivery_per_producer"]
    production_cost = params["production_cost"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j]: energy delivered by producer i to contract j
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{j}")
          for j in range(num_contracts)]
         for i in range(num_producers)]

    # y[i][j]: binary, 1 if producer i contributes to contract j
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")
          for j in range(num_contracts)]
         for i in range(num_producers)]

    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(
            production_cost[i][j] * x[i][j]
            for i in range(num_producers)
            for j in range(num_contracts)
        ),
        GRB.MINIMIZE
    )

    # Producer capacity constraints
    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_contracts)) <= producer_capacity[i],
            name=f"cap_{i}"
        )

    # Contract demand constraints
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_producers)) >= contract_demand[j],
            name=f"demand_{j}"
        )

    # Minimum number of producers per contract
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i][j] for i in range(num_producers)) >= min_producers_per_contract,
            name=f"min_prod_{j}"
        )

    # Minimum delivery if contributing, and linking x to y
    for i in range(num_producers):
        for j in range(num_contracts):
            # x[i][j] >= min_delivery * y[i][j]
            model.addConstr(
                x[i][j] >= min_delivery_per_producer[i] * y[i][j],
                name=f"min_del_{i}_{j}"
            )
            # x[i][j] <= capacity * y[i][j]  (y=0 forces x=0)
            model.addConstr(
                x[i][j] <= producer_capacity[i] * y[i][j],
                name=f"link_{i}_{j}"
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
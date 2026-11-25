import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_origins = 4
    n_dests = 5
    n_products = 2

    supply = [
        [params["supply_origin0_product0"], params["supply_origin0_product1"]],
        [params["supply_origin1_product0"], params["supply_origin1_product1"]],
        [params["supply_origin2_product0"], params["supply_origin2_product1"]],
        [params["supply_origin3_product0"], params["supply_origin3_product1"]],
    ]

    demand = [
        [params["demand_dest0_product0"], params["demand_dest0_product1"]],
        [params["demand_dest1_product0"], params["demand_dest1_product1"]],
        [params["demand_dest2_product0"], params["demand_dest2_product1"]],
        [params["demand_dest3_product0"], params["demand_dest3_product1"]],
        [params["demand_dest4_product0"], params["demand_dest4_product1"]],
    ]

    cost = params["cost_matrix"]       # [origin][dest][product]
    capacity = params["capacity_matrix"]  # [origin][dest]

    model = gp.Model()
    model.Params.OutputFlag = 0

    # Decision variables: x[i][j][k] = units of product k from origin i to dest j
    x = [
        [
            [model.addVar(lb=0.0, name=f"x_{i}_{j}_{k}") for k in range(n_products)]
            for j in range(n_dests)
        ]
        for i in range(n_origins)
    ]

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(
            cost[i][j][k] * x[i][j][k]
            for i in range(n_origins)
            for j in range(n_dests)
            for k in range(n_products)
        ),
        GRB.MINIMIZE
    )

    # Supply constraints: all supply must be fully allocated
    for i in range(n_origins):
        for k in range(n_products):
            model.addConstr(
                gp.quicksum(x[i][j][k] for j in range(n_dests)) == supply[i][k],
                name=f"supply_{i}_{k}"
            )

    # Demand constraints: all demand must be fully satisfied
    for j in range(n_dests):
        for k in range(n_products):
            model.addConstr(
                gp.quicksum(x[i][j][k] for i in range(n_origins)) == demand[j][k],
                name=f"demand_{j}_{k}"
            )

    # Capacity constraints: combined shipment per origin-dest pair
    for i in range(n_origins):
        for j in range(n_dests):
            model.addConstr(
                gp.quicksum(x[i][j][k] for k in range(n_products)) <= capacity[i][j],
                name=f"capacity_{i}_{j}"
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
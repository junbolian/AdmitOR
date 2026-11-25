import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = [params["profit_product0"], params["profit_product1"]]
    holding_cost = params["holding_cost"]
    grinder_req = [params["grinder_req_product0"], params["grinder_req_product1"]]
    drill_req = [params["drill_req_product0"], params["drill_req_product1"]]
    borer_req = [params["borer_req_product0"], params["borer_req_product1"]]
    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit = [params["sales_limit_product0"], params["sales_limit_product1"]]
    target_inv = [params["target_inventory_product0"], params["target_inventory_product1"]]

    products = [0, 1]
    periods = [0, 1, 2, 3]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = {(p, t): model.addVar(lb=0, name=f"produce_{p}_{t}")
               for p in products for t in periods}
    inventory = {(p, t): model.addVar(lb=0, ub=inventory_limit, name=f"inventory_{p}_{t}")
                 for p in products for t in periods}
    sales = {(p, t): model.addVar(lb=0, ub=sales_limit[p][t], name=f"sales_{p}_{t}")
             for p in products for t in periods}

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(produce[p, t] == sales[p, t] + inventory[p, t],
                                name=f"balance_{p}_{t}")
            else:
                model.addConstr(inventory[p, t - 1] + produce[p, t] == sales[p, t] + inventory[p, t],
                                name=f"balance_{p}_{t}")

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_req[p] * produce[p, t] for p in products) <= grinder_cap[t],
            name=f"grinder_{t}"
        )
        model.addConstr(
            gp.quicksum(drill_req[p] * produce[p, t] for p in products) <= drill_cap[t],
            name=f"drill_{t}"
        )
        model.addConstr(
            gp.quicksum(borer_req[p] * produce[p, t] for p in products) <= borer_cap[t],
            name=f"borer_{t}"
        )

    # Target inventory at end of period 3
    for p in products:
        model.addConstr(inventory[p, 3] == target_inv[p], name=f"target_inv_{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
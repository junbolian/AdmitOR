import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_p0 = params["supply_product0"]  # list of length 5
    supply_p1 = params["supply_product1"]  # list of length 5
    demand_p0 = params["demand_product0"]  # list of length 6
    demand_p1 = params["demand_product1"]  # list of length 6
    cost_p0 = params["transport_cost_product0"]  # 5x6
    cost_p1 = params["transport_cost_product1"]  # 5x6
    link_cap = params["link_capacity"]  # 5x6

    W = range(5)
    S = range(6)

    model = gp.Model("multi_product_transport")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[p][w][s] = units of product p shipped from warehouse w to store s
    x0 = model.addVars(W, S, lb=0.0, name="x0")
    x1 = model.addVars(W, S, lb=0.0, name="x1")

    # Objective: minimize total transportation cost
    obj = gp.quicksum(cost_p0[w][s] * x0[w, s] + cost_p1[w][s] * x1[w, s]
                      for w in W for s in S)
    model.setObjective(obj, GRB.MINIMIZE)

    # Supply constraints
    for w in W:
        model.addConstr(gp.quicksum(x0[w, s] for s in S) <= supply_p0[w], name=f"sup_p0_w{w}")
        model.addConstr(gp.quicksum(x1[w, s] for s in S) <= supply_p1[w], name=f"sup_p1_w{w}")

    # Demand constraints
    for s in S:
        model.addConstr(gp.quicksum(x0[w, s] for w in W) >= demand_p0[s], name=f"dem_p0_s{s}")
        model.addConstr(gp.quicksum(x1[w, s] for w in W) >= demand_p1[s], name=f"dem_p1_s{s}")

    # Link capacity constraints
    for w in W:
        for s in S:
            model.addConstr(x0[w, s] + x1[w, s] <= link_cap[w][s], name=f"cap_w{w}_s{s}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
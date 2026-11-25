import gurobipy as gp
from gurobipy import GRB

def solve(params):
    transport_cost = params["transport_cost_per_unit"]
    
    net_supply = {
        (0, 0): params["net_supply_product0_city0"],
        (1, 0): params["net_supply_product1_city0"],
        (0, 1): params["net_supply_product0_city1"],
        (1, 1): params["net_supply_product1_city1"],
        (0, 2): params["net_supply_product0_city2"],
        (1, 2): params["net_supply_product1_city2"],
        (0, 3): params["net_supply_product0_city3"],
        (1, 3): params["net_supply_product1_city3"],
    }
    
    total_cap = params["total_shipping_capacity_any_pair"]
    cap_p0_01 = params["capacity_product0_city0_city1"]
    cap_p1_01 = params["capacity_product1_city0_city1"]
    cap_p0_23 = params["capacity_product0_city2_city3"]
    cap_p1_23 = params["capacity_product1_city2_city3"]
    
    cities = [0, 1, 2, 3]
    products = [0, 1]
    city_pairs = [(i, j) for i in cities for j in cities if i < j]
    
    model = gp.Model("transport")
    model.setParam("OutputFlag", 0)
    
    x = {}
    for p in products:
        for i in cities:
            for j in cities:
                if i != j:
                    x[p, i, j] = model.addVar(lb=0.0, name=f"x_{p}_{i}_{j}")
    
    model.update()
    
    model.setObjective(
        transport_cost * gp.quicksum(x[p, i, j] for p in products for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )
    
    # Flow balance: inflow - outflow = net_supply (positive net_supply means net receiver/demand)
    # If net_supply > 0 means the city is a net consumer (demand), it receives more than it sends
    # Try both sign conventions by using: net inflow = net_supply
    for p in products:
        for i in cities:
            inflow = gp.quicksum(x[p, j, i] for j in cities if j != i)
            outflow = gp.quicksum(x[p, i, j] for j in cities if j != i)
            model.addConstr(inflow - outflow == net_supply[p, i], name=f"balance_p{p}_c{i}")
    
    for (i, j) in city_pairs:
        model.addConstr(
            gp.quicksum(x[p, i, j] + x[p, j, i] for p in products) <= total_cap,
            name=f"total_cap_{i}_{j}"
        )
    
    model.addConstr(x[0, 0, 1] + x[0, 1, 0] <= cap_p0_01, name="cap_p0_01")
    model.addConstr(x[1, 0, 1] + x[1, 1, 0] <= cap_p1_01, name="cap_p1_01")
    model.addConstr(x[0, 2, 3] + x[0, 3, 2] <= cap_p0_23, name="cap_p0_23")
    model.addConstr(x[1, 2, 3] + x[1, 3, 2] <= cap_p1_23, name="cap_p1_23")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
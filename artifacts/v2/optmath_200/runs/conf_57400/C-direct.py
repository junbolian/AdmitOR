import gurobipy as gp
from gurobipy import GRB

def solve(params):
    shipping_cost = params["shipping_cost"]
    
    # Net demand/supply values (positive = demand/inflow needed, for supply it's excess outflow)
    net_demand_prod0_city0 = params["net_demand_prod0_city0"]
    net_supply_prod1_city0 = params["net_supply_prod1_city0"]
    net_demand_prod0_city1 = params["net_demand_prod0_city1"]
    net_demand_prod1_city1 = params["net_demand_prod1_city1"]
    net_supply_prod0_city2 = params["net_supply_prod0_city2"]
    net_demand_prod1_city2 = params["net_demand_prod1_city2"]
    
    joint_capacity = params["joint_capacity"]
    
    # Product-specific capacities
    prod_cap = {
        (0, 1, 0): params["prod_cap_01_p0"],
        (0, 1, 1): params["prod_cap_01_p1"],
        (0, 2, 0): params["prod_cap_02_p0"],
        (0, 2, 1): params["prod_cap_02_p1"],
        (1, 0, 0): params["prod_cap_10_p0"],
        (1, 0, 1): params["prod_cap_10_p1"],
        (1, 2, 0): params["prod_cap_12_p0"],
        (1, 2, 1): params["prod_cap_12_p1"],
        (2, 0, 0): params["prod_cap_20_p0"],
        (2, 0, 1): params["prod_cap_20_p1"],
        (2, 1, 0): params["prod_cap_21_p0"],
        (2, 1, 1): params["prod_cap_21_p1"],
    }
    
    cities = [0, 1, 2]
    products = [0, 1]
    arcs = [(i, j) for i in cities for j in cities if i != j]
    
    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)
    
    # Decision variables: x[i, j, p] = units of product p shipped from city i to city j
    x = {}
    for (i, j) in arcs:
        for p in products:
            x[i, j, p] = model.addVar(lb=0.0, name=f"x_{i}_{j}_{p}")
    
    # Objective: minimize total shipping cost
    model.setObjective(
        shipping_cost * gp.quicksum(x[i, j, p] for (i, j) in arcs for p in products),
        GRB.MINIMIZE
    )
    
    # Flow balance constraints
    # For each city and product: inflow - outflow = net_demand (positive) or -net_supply (negative)
    # net_demand > 0: city needs inflow  => inflow - outflow = net_demand
    # net_supply > 0: city has excess    => inflow - outflow = -net_supply
    
    balance = {
        (0, 0): net_demand_prod0_city0,    # City 0, Product 0: needs inflow of 3
        (0, 1): -net_supply_prod1_city0,   # City 0, Product 1: needs outflow of 2
        (1, 0): net_demand_prod0_city1,    # City 1, Product 0: balanced (0)
        (1, 1): net_demand_prod1_city1,    # City 1, Product 1: needs inflow of 1
        (2, 0): -net_supply_prod0_city2,   # City 2, Product 0: needs outflow of 3
        (2, 1): net_demand_prod1_city2,    # City 2, Product 1: needs inflow of 1
    }
    
    for city in cities:
        for p in products:
            inflow = gp.quicksum(x[i, city, p] for i in cities if i != city)
            outflow = gp.quicksum(x[city, j, p] for j in cities if j != city)
            rhs = balance[(city, p)]
            model.addConstr(inflow - outflow == rhs, name=f"balance_{city}_{p}")
    
    # Joint capacity constraints
    for (i, j) in arcs:
        model.addConstr(
            gp.quicksum(x[i, j, p] for p in products) <= joint_capacity,
            name=f"joint_cap_{i}_{j}"
        )
    
    # Product-specific capacity constraints
    for (i, j) in arcs:
        for p in products:
            model.addConstr(
                x[i, j, p] <= prod_cap[(i, j, p)],
                name=f"prod_cap_{i}_{j}_{p}"
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
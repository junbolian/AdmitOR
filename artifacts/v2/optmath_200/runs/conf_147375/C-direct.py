import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    shipping_cost = params["shipping_cost_per_unit"]
    joint_cap = params["joint_capacity"]
    
    pc_0_0to1 = params["product_capacity_0_0to1"]
    pc_1_0to1 = params["product_capacity_1_0to1"]
    pc_0_1to0 = params["product_capacity_0_1to0"]
    pc_1_1to0 = params["product_capacity_1_1to0"]
    pc_low = params["product_capacity_generic_low"]
    pc_high = params["product_capacity_generic_high"]
    
    demand_c1_p0 = params["demand_city1_product0"]
    demand_c1_p1 = params["demand_city1_product1"]
    demand_c2_p0 = params["demand_city2_product0"]
    supply_c2_p1 = params["supply_city2_product1"]
    supply_c3_p0 = params["supply_city3_product0"]
    demand_c3_p1 = params["demand_city3_product1"]

    # Cities: 0, 1, 2, 3
    # Products: 0, 1
    # Arcs: all ordered pairs (i, j) with i != j
    cities = [0, 1, 2, 3]
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

    # Joint capacity constraints: sum of both products on each arc <= joint_cap
    for (i, j) in arcs:
        model.addConstr(
            gp.quicksum(x[i, j, p] for p in products) <= joint_cap,
            name=f"joint_{i}_{j}"
        )

    # Product-specific capacity constraints
    # Helper function to get capacity for arc (i,j) and product p
    def get_product_cap(i, j, p):
        if (i, j) == (0, 1):
            return pc_0_0to1 if p == 0 else pc_1_0to1
        elif (i, j) == (1, 0):
            return pc_0_1to0 if p == 0 else pc_1_1to0
        else:
            # Generic: use varying limits
            # We use a deterministic mapping based on arc index and product
            arc_list = [(i2, j2) for i2 in cities for j2 in cities if i2 != j2]
            idx = arc_list.index((i, j))
            # Alternate between low and high based on index + product
            seed = idx * 2 + p
            if seed % 2 == 0:
                return pc_high
            else:
                return pc_low

    for (i, j) in arcs:
        for p in products:
            cap = get_product_cap(i, j, p)
            model.addConstr(
                x[i, j, p] <= cap,
                name=f"prodcap_{i}_{j}_{p}"
            )

    # Flow balance constraints
    # net[city][product]: positive = demand (inflow needed), negative = supply (outflow needed)
    # City 0: no net supply or demand
    # City 1: demand 3 of P0, demand 1 of P1
    # City 2: demand 1 of P0, supply 1 of P1 (excess = outflow)
    # City 3: supply 4 of P0 (excess = outflow), demand 0 of P1
    # Convention: net_demand[c][p] = demand - supply
    # Flow balance: inflow - outflow = net_demand[c][p]
    
    net_demand = {
        0: {0: 0.0, 1: 0.0},
        1: {0: demand_c1_p0, 1: demand_c1_p1},
        2: {0: demand_c2_p0, 1: -supply_c2_p1},
        3: {0: -supply_c3_p0, 1: demand_c3_p1},
    }

    for c in cities:
        for p in products:
            inflow = gp.quicksum(x[i, c, p] for i in cities if i != c)
            outflow = gp.quicksum(x[c, j, p] for j in cities if j != c)
            model.addConstr(
                inflow - outflow == net_demand[c][p],
                name=f"flow_{c}_{p}"
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
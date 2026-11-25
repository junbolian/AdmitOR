import gurobipy as gp
from gurobipy import GRB

def solve(params):
    transport_cost = params["transport_cost_per_unit"]
    joint_cap = params["joint_capacity_per_pair"]

    num_cities = 4
    num_products = 2
    cities = range(num_cities)
    products = range(num_products)

    # Net flow requirements: net_flow[c][p]
    net_flow = {
        0: {0: params["net_flow_city0_product0"], 1: params["net_flow_city0_product1"]},
        1: {0: params["net_flow_city1_product0"], 1: params["net_flow_city1_product1"]},
        2: {0: params["net_flow_city2_product0"], 1: params["net_flow_city2_product1"]},
        3: {0: params["net_flow_city3_product0"], 1: params["net_flow_city3_product1"]},
    }

    # Product-specific capacities: prod_cap[(i,j,p)]
    prod_cap = {}
    for i in cities:
        for j in cities:
            if i == j:
                continue
            for p in products:
                key = f"product{p}_capacity_city{i}_city{j}"
                prod_cap[(i, j, p)] = params[key]

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j,p] = units of product p shipped from city i to city j
    x = {}
    for i in cities:
        for j in cities:
            if i == j:
                continue
            for p in products:
                x[(i, j, p)] = model.addVar(lb=0.0, ub=prod_cap[(i, j, p)],
                                             vtype=GRB.CONTINUOUS,
                                             name=f"x_{i}_{j}_{p}")

    # Objective: minimize total transport cost
    model.setObjective(
        transport_cost * gp.quicksum(x[(i, j, p)]
                                     for i in cities for j in cities if i != j
                                     for p in products),
        GRB.MINIMIZE
    )

    # Flow balance constraints: outflow - inflow = net_flow[c][p]
    for c in cities:
        for p in products:
            outflow = gp.quicksum(x[(c, j, p)] for j in cities if j != c)
            inflow = gp.quicksum(x[(i, c, p)] for i in cities if i != c)
            model.addConstr(outflow - inflow == net_flow[c][p],
                            name=f"flow_balance_c{c}_p{p}")

    # Joint capacity constraints
    for i in cities:
        for j in cities:
            if i == j:
                continue
            model.addConstr(
                gp.quicksum(x[(i, j, p)] for p in products) <= joint_cap,
                name=f"joint_cap_{i}_{j}"
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
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    octane_rating    = params["octane_rating"]       # list of 4 octane values
    raw_availability = params["raw_availability"]    # list of 4 availability limits
    raw_cost         = params["raw_cost"]            # list of 4 costs per barrel
    min_octane_product = params["min_octane_product"] # list of 2 min octane [regular, premium]
    selling_price    = params["selling_price"]       # list of 2 prices [regular, premium]
    max_demand       = params["max_demand"]          # list of 2 demand limits [regular, premium]

    # Index sets
    raws     = range(4)   # raw gasolines 0..3
    products = range(2)   # 0 = regular, 1 = premium

    model = gp.Model("solar_oil")
    model.setParam("OutputFlag", 0)

    # x[i, j] = barrels of raw gasoline i blended into product j
    x = model.addVars(raws, products, lb=0.0, name="x")

    # Total barrels of each product j
    vol = {j: gp.quicksum(x[i, j] for i in raws) for j in products}

    # --- Constraints ---

    # Raw gasoline availability
    for i in raws:
        model.addConstr(
            gp.quicksum(x[i, j] for j in products) <= raw_availability[i],
            name=f"avail_{i}"
        )

    # Maximum demand for each product
    for j in products:
        model.addConstr(vol[j] <= max_demand[j], name=f"demand_{j}")

    # Minimum octane requirement for each product (linearised):
    #   sum_i octane[i]*x[i,j] >= min_octane[j] * sum_i x[i,j]
    for j in products:
        model.addConstr(
            gp.quicksum(octane_rating[i] * x[i, j] for i in raws)
            >= min_octane_product[j] * vol[j],
            name=f"octane_{j}"
        )

    # --- Objective: maximise profit = revenue - raw material cost ---
    revenue     = gp.quicksum(selling_price[j] * vol[j] for j in products)
    raw_mat_cost = gp.quicksum(raw_cost[i] * x[i, j] for i in raws for j in products)

    model.setObjective(revenue - raw_mat_cost, GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}
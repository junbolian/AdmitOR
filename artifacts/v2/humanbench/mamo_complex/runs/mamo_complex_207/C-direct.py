import gurobipy as gp
from gurobipy import GRB

def solve(params):
    octane_raw = [
        params["octane_raw_1"],
        params["octane_raw_2"],
        params["octane_raw_3"],
        params["octane_raw_4"],
    ]
    availability_raw = [
        params["availability_raw_1"],
        params["availability_raw_2"],
        params["availability_raw_3"],
        params["availability_raw_4"],
    ]
    cost_raw = [
        params["cost_raw_1"],
        params["cost_raw_2"],
        params["cost_raw_3"],
        params["cost_raw_4"],
    ]
    octane_min_regular = params["octane_min_regular"]
    octane_min_premium = params["octane_min_premium"]
    price_regular = params["price_regular"]
    price_premium = params["price_premium"]
    demand_max_regular = params["demand_max_regular"]
    demand_max_premium = params["demand_max_premium"]

    # Indices: raws 0..3, products: 0=regular, 1=premium
    raws = range(4)

    model = gp.Model("solar_oil")
    model.setParam("OutputFlag", 0)

    # x[i, p]: barrels of raw i blended into product p (0=regular, 1=premium)
    x = {}
    for i in raws:
        for p in range(2):
            x[i, p] = model.addVar(lb=0.0, name=f"x_{i}_{p}")

    # Total volume of each product
    vol_regular = gp.quicksum(x[i, 0] for i in raws)
    vol_premium = gp.quicksum(x[i, 1] for i in raws)

    # Demand constraints
    model.addConstr(vol_regular <= demand_max_regular, name="demand_regular")
    model.addConstr(vol_premium <= demand_max_premium, name="demand_premium")

    # Availability constraints for each raw gasoline
    for i in raws:
        model.addConstr(
            x[i, 0] + x[i, 1] <= availability_raw[i],
            name=f"avail_{i}"
        )

    # Octane constraints (linearized form):
    # sum(octane_raw[i] * x[i, p]) >= octane_min_p * sum(x[i, p])
    # => sum((octane_raw[i] - octane_min_p) * x[i, p]) >= 0
    model.addConstr(
        gp.quicksum((octane_raw[i] - octane_min_regular) * x[i, 0] for i in raws) >= 0,
        name="octane_regular"
    )
    model.addConstr(
        gp.quicksum((octane_raw[i] - octane_min_premium) * x[i, 1] for i in raws) >= 0,
        name="octane_premium"
    )

    # Objective: revenue - raw material cost
    revenue = price_regular * vol_regular + price_premium * vol_premium
    raw_cost = gp.quicksum(cost_raw[i] * (x[i, 0] + x[i, 1]) for i in raws)
    model.setObjective(revenue - raw_cost, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    raws = ["A", "B", "C"]
    candies = [1, 2, 3]

    raw_cost = {
        "A": params["raw_cost_A"],
        "B": params["raw_cost_B"],
        "C": params["raw_cost_C"],
    }
    raw_limit = {
        "A": params["limit_A"],
        "B": params["limit_B"],
        "C": params["limit_C"],
    }
    proc_fee = {1: params["proc_fee_1"], 2: params["proc_fee_2"], 3: params["proc_fee_3"]}
    price = {1: params["price_1"], 2: params["price_2"], 3: params["price_3"]}

    model = gp.Model("candy_factory")
    model.Params.OutputFlag = 0

    # x[i, j] = kg of raw material j blended into candy type i
    x = model.addVars(candies, raws, lb=0.0, name="x")
    # y[i] = total kg of candy type i produced
    y = model.addVars(candies, lb=0.0, name="y")

    # Blend definition: total candy output equals sum of its raw inputs
    for i in candies:
        model.addConstr(
            gp.quicksum(x[i, j] for j in raws) == y[i],
            name=f"blend_def_{i}",
        )

    # Monthly raw material availability
    for j in raws:
        model.addConstr(
            gp.quicksum(x[i, j] for i in candies) <= raw_limit[j],
            name=f"raw_limit_{j}",
        )

    # Composition requirements
    # Candy 1: minimum fraction of raw A, maximum fraction of raw C
    model.addConstr(
        x[1, "A"] >= params["content_A_min_1"] * y[1], name="content_A_min_1"
    )
    model.addConstr(
        x[1, "C"] <= params["content_C_max_1"] * y[1], name="content_C_max_1"
    )
    # Candy 2: minimum fraction of raw B, maximum fraction of raw C
    model.addConstr(
        x[2, "B"] >= params["content_B_min_2"] * y[2], name="content_B_min_2"
    )
    model.addConstr(
        x[2, "C"] <= params["content_C_max_2"] * y[2], name="content_C_max_2"
    )
    # Candy 3: maximum fraction of raw C
    model.addConstr(
        x[3, "C"] <= params["content_C_max_3"] * y[3], name="content_C_max_3"
    )

    # Revenue from candy sales minus processing fees minus raw material costs
    revenue = gp.quicksum(price[i] * y[i] for i in candies)
    processing = gp.quicksum(proc_fee[i] * y[i] for i in candies)
    material = gp.quicksum(raw_cost[j] * x[i, j] for i in candies for j in raws)

    model.setObjective(revenue - processing - material, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.Status}"}
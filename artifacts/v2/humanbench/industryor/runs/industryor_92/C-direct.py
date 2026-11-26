import gurobipy as gp
from gurobipy import GRB

def solve(params):
    time_A1_I   = params["time_A1_I"]
    time_A1_II  = params["time_A1_II"]
    time_A2_I   = params["time_A2_I"]
    time_A2_II  = params["time_A2_II"]
    time_A2_III = params["time_A2_III"]
    time_B1_I   = params["time_B1_I"]
    time_B1_II  = params["time_B1_II"]
    time_B2_I   = params["time_B2_I"]
    time_B2_III = params["time_B2_III"]
    time_B3_I   = params["time_B3_I"]
    cap_A1 = params["cap_A1"]
    cap_A2 = params["cap_A2"]
    cap_B1 = params["cap_B1"]
    cap_B2 = params["cap_B2"]
    cap_B3 = params["cap_B3"]
    cost_A1 = params["cost_A1"]
    cost_A2 = params["cost_A2"]
    cost_B1 = params["cost_B1"]
    cost_B2 = params["cost_B2"]
    cost_B3 = params["cost_B3"]
    raw_I   = params["raw_I"]
    raw_II  = params["raw_II"]
    raw_III = params["raw_III"]
    price_I   = params["price_I"]
    price_II  = params["price_II"]
    price_III = params["price_III"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: how many units of each product processed on each
    # eligible (procedure, equipment) combination.
    #
    # Procedure A:
    #   x_A1_I  : units of product I processed on A1
    #   x_A1_II : units of product II processed on A1
    #   x_A2_I  : units of product I processed on A2
    #   x_A2_II : units of product II processed on A2
    #   x_A2_III: units of product III processed on A2
    #
    # Procedure B:
    #   x_B1_I  : units of product I processed on B1
    #   x_B1_II : units of product II processed on B1
    #   x_B2_I  : units of product I processed on B2
    #   x_B2_III: units of product III processed on B2
    #   x_B3_I  : units of product I processed on B3

    x_A1_I   = model.addVar(lb=0, name="x_A1_I")
    x_A1_II  = model.addVar(lb=0, name="x_A1_II")
    x_A2_I   = model.addVar(lb=0, name="x_A2_I")
    x_A2_II  = model.addVar(lb=0, name="x_A2_II")
    x_A2_III = model.addVar(lb=0, name="x_A2_III")

    x_B1_I   = model.addVar(lb=0, name="x_B1_I")
    x_B1_II  = model.addVar(lb=0, name="x_B1_II")
    x_B2_I   = model.addVar(lb=0, name="x_B2_I")
    x_B2_III = model.addVar(lb=0, name="x_B2_III")
    x_B3_I   = model.addVar(lb=0, name="x_B3_I")

    # Total production of each product (must be consistent across both procedures)
    # Product I total through A = total through B
    total_A_I   = x_A1_I + x_A2_I
    total_A_II  = x_A1_II + x_A2_II
    total_A_III = x_A2_III

    total_B_I   = x_B1_I + x_B2_I + x_B3_I
    total_B_II  = x_B1_II
    total_B_III = x_B2_III

    # Flow balance: units entering procedure A must equal units leaving procedure B
    model.addConstr(total_A_I   == total_B_I,   name="balance_I")
    model.addConstr(total_A_II  == total_B_II,  name="balance_II")
    model.addConstr(total_A_III == total_B_III, name="balance_III")

    # Capacity constraints
    model.addConstr(
        time_A1_I * x_A1_I + time_A1_II * x_A1_II <= cap_A1, name="cap_A1"
    )
    model.addConstr(
        time_A2_I * x_A2_I + time_A2_II * x_A2_II + time_A2_III * x_A2_III <= cap_A2,
        name="cap_A2"
    )
    model.addConstr(
        time_B1_I * x_B1_I + time_B1_II * x_B1_II <= cap_B1, name="cap_B1"
    )
    model.addConstr(
        time_B2_I * x_B2_I + time_B2_III * x_B2_III <= cap_B2, name="cap_B2"
    )
    model.addConstr(
        time_B3_I * x_B3_I <= cap_B3, name="cap_B3"
    )

    # Equipment cost rates (cost per unit time = cost_at_full_load / capacity)
    rate_A1 = cost_A1 / cap_A1
    rate_A2 = cost_A2 / cap_A2
    rate_B1 = cost_B1 / cap_B1
    rate_B2 = cost_B2 / cap_B2
    rate_B3 = cost_B3 / cap_B3

    # Equipment costs
    equip_cost = (
        rate_A1 * (time_A1_I * x_A1_I + time_A1_II * x_A1_II)
        + rate_A2 * (time_A2_I * x_A2_I + time_A2_II * x_A2_II + time_A2_III * x_A2_III)
        + rate_B1 * (time_B1_I * x_B1_I + time_B1_II * x_B1_II)
        + rate_B2 * (time_B2_I * x_B2_I + time_B2_III * x_B2_III)
        + rate_B3 * (time_B3_I * x_B3_I)
    )

    # Raw material costs
    raw_cost = (
        raw_I   * total_A_I
        + raw_II  * total_A_II
        + raw_III * total_A_III
    )

    # Revenue
    revenue = (
        price_I   * total_A_I
        + price_II  * total_A_II
        + price_III * total_A_III
    )

    # Profit = revenue - raw material cost - equipment cost
    profit = revenue - raw_cost - equip_cost

    model.setObjective(profit, GRB.MAXIMIZE)

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
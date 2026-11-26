import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_gas_I = params["price_gas_I"]
    price_gas_II = params["price_gas_II"]
    min_prop_A_I = params["min_prop_A_I"]
    min_prop_A_II = params["min_prop_A_II"]
    inventory_A = params["inventory_A"]
    inventory_B = params["inventory_B"]
    max_purchase_A = params["max_purchase_A"]
    price_tier1 = params["price_tier1"]
    tier1_limit = params["tier1_limit"]
    price_tier2 = params["price_tier2"]
    tier2_limit = params["tier2_limit"]
    price_tier3 = params["price_tier3"]

    model = gp.Model("crude_blending")
    model.setParam("OutputFlag", 0)

    # Amount of crude A used in gasoline Type I and Type II
    aI = model.addVar(lb=0, name="aI")   # crude A in gasoline I
    bI = model.addVar(lb=0, name="bI")   # crude B in gasoline I
    aII = model.addVar(lb=0, name="aII") # crude A in gasoline II
    bII = model.addVar(lb=0, name="bII") # crude B in gasoline II

    # Tiered purchasing of crude A
    t1 = model.addVar(lb=0, ub=tier1_limit, name="t1")
    t2 = model.addVar(lb=0, ub=(tier2_limit - tier1_limit), name="t2")
    t3 = model.addVar(lb=0, name="t3")

    model.update()

    # Total crude A purchased
    purchase_A = t1 + t2 + t3

    # Total crude A available
    total_A = inventory_A + purchase_A

    # Total crude B available
    total_B = inventory_B

    # Supply constraints
    model.addConstr(aI + aII <= total_A, name="supply_A")
    model.addConstr(bI + bII <= total_B, name="supply_B")

    # Maximum purchase constraint
    model.addConstr(purchase_A <= max_purchase_A, name="max_purchase")

    # Minimum proportion of crude A in gasoline Type I
    # aI / (aI + bI) >= min_prop_A_I  =>  aI >= min_prop_A_I * (aI + bI)
    # aI * (1 - min_prop_A_I) >= min_prop_A_I * bI
    model.addConstr(aI * (1 - min_prop_A_I) >= min_prop_A_I * bI, name="prop_I")

    # Minimum proportion of crude A in gasoline Type II
    model.addConstr(aII * (1 - min_prop_A_II) >= min_prop_A_II * bII, name="prop_II")

    # Revenue
    revenue = price_gas_I * (aI + bI) + price_gas_II * (aII + bII)

    # Purchasing cost (tiered)
    purchase_cost = price_tier1 * t1 + price_tier2 * t2 + price_tier3 * t3

    # Profit = revenue - purchase cost
    profit = revenue - purchase_cost

    model.setObjective(profit, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
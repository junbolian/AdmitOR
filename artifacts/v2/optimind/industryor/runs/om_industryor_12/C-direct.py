import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_corn = params["profit_corn"]
    profit_wheat = params["profit_wheat"]
    profit_soybeans = params["profit_soybeans"]
    profit_sorghum = params["profit_sorghum"]
    total_land = params["total_land"]
    corn_to_wheat_min_ratio = params["corn_to_wheat_min_ratio"]
    soybean_to_sorghum_min_ratio = params["soybean_to_sorghum_min_ratio"]
    wheat_to_sorghum_ratio = params["wheat_to_sorghum_ratio"]

    model = gp.Model("farm_allocation")
    model.setParam("OutputFlag", 0)

    corn = model.addVar(lb=0.0, name="corn")
    wheat = model.addVar(lb=0.0, name="wheat")
    soybeans = model.addVar(lb=0.0, name="soybeans")
    sorghum = model.addVar(lb=0.0, name="sorghum")

    model.setObjective(
        profit_corn * corn + profit_wheat * wheat + profit_soybeans * soybeans + profit_sorghum * sorghum,
        GRB.MAXIMIZE
    )

    model.addConstr(corn + wheat + soybeans + sorghum <= total_land, name="total_land")
    model.addConstr(corn >= corn_to_wheat_min_ratio * wheat, name="corn_wheat_ratio")
    model.addConstr(soybeans >= soybean_to_sorghum_min_ratio * sorghum, name="soy_sorghum_ratio")
    model.addConstr(wheat == wheat_to_sorghum_ratio * sorghum, name="wheat_sorghum_ratio")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
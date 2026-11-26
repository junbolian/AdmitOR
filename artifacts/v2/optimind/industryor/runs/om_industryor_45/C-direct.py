import gurobipy as gp
from gurobipy import GRB

def solve(params):
    land_capacity = params["land_capacity"]
    funds_capacity = params["funds_capacity"]
    labor_autumn_winter = params["labor_autumn_winter"]
    labor_spring_summer = params["labor_spring_summer"]
    external_wage_spring_summer = params["external_wage_spring_summer"]
    external_wage_autumn_winter = params["external_wage_autumn_winter"]
    cow_investment = params["cow_investment"]
    chicken_investment = params["chicken_investment"]
    cow_land = params["cow_land"]
    cow_labor_autumn_winter = params["cow_labor_autumn_winter"]
    cow_labor_spring_summer = params["cow_labor_spring_summer"]
    cow_net_income = params["cow_net_income"]
    chicken_labor_autumn_winter = params["chicken_labor_autumn_winter"]
    chicken_labor_spring_summer = params["chicken_labor_spring_summer"]
    chicken_net_income = params["chicken_net_income"]
    chicken_capacity = params["chicken_capacity"]
    cow_capacity = params["cow_capacity"]
    soybean_labor_autumn_winter = params["soybean_labor_autumn_winter"]
    soybean_labor_spring_summer = params["soybean_labor_spring_summer"]
    soybean_net_income = params["soybean_net_income"]
    corn_labor_autumn_winter = params["corn_labor_autumn_winter"]
    corn_labor_spring_summer = params["corn_labor_spring_summer"]
    corn_net_income = params["corn_net_income"]
    wheat_labor_autumn_winter = params["wheat_labor_autumn_winter"]
    wheat_labor_spring_summer = params["wheat_labor_spring_summer"]
    wheat_net_income = params["wheat_net_income"]

    model = gp.Model("farm_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # Crop areas (continuous, hectares)
    soybean = model.addVar(lb=0.0, name="soybean")
    corn = model.addVar(lb=0.0, name="corn")
    wheat = model.addVar(lb=0.0, name="wheat")

    # Animal counts (integer)
    cows = model.addVar(lb=0, ub=cow_capacity, vtype=GRB.INTEGER, name="cows")
    chickens = model.addVar(lb=0, ub=chicken_capacity, vtype=GRB.INTEGER, name="chickens")

    # External labor (integer person-days, non-negative)
    ext_aw = model.addVar(lb=0, vtype=GRB.INTEGER, name="ext_aw")
    ext_ss = model.addVar(lb=0, vtype=GRB.INTEGER, name="ext_ss")

    # Land constraint: crop area + feed land for cows <= total land
    model.addConstr(
        soybean + corn + wheat + cow_land * cows <= land_capacity,
        name="land"
    )

    # Funds constraint: animal investments <= funds
    model.addConstr(
        cow_investment * cows + chicken_investment * chickens <= funds_capacity,
        name="funds"
    )

    # Autumn/winter labor constraint: labor used on farm + external labor <= available
    model.addConstr(
        soybean_labor_autumn_winter * soybean
        + corn_labor_autumn_winter * corn
        + wheat_labor_autumn_winter * wheat
        + cow_labor_autumn_winter * cows
        + chicken_labor_autumn_winter * chickens
        + ext_aw <= labor_autumn_winter,
        name="labor_aw"
    )

    # Spring/summer labor constraint
    model.addConstr(
        soybean_labor_spring_summer * soybean
        + corn_labor_spring_summer * corn
        + wheat_labor_spring_summer * wheat
        + cow_labor_spring_summer * cows
        + chicken_labor_spring_summer * chickens
        + ext_ss <= labor_spring_summer,
        name="labor_ss"
    )

    # Objective: maximize total annual net income
    # = crop income + animal income + external labor income
    obj = (
        soybean_net_income * soybean
        + corn_net_income * corn
        + wheat_net_income * wheat
        + cow_net_income * cows
        + chicken_net_income * chickens
        + external_wage_autumn_winter * ext_aw
        + external_wage_spring_summer * ext_ss
    )
    model.setObjective(obj, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}
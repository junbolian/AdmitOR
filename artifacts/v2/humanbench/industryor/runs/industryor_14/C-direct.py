import gurobipy as gp
from gurobipy import GRB


def solve(params):
    land_capacity = params["land_capacity"]
    capital_budget = params["capital_budget"]
    labor_aw_capacity = params["labor_aw_capacity"]
    labor_ss_capacity = params["labor_ss_capacity"]
    wage_hire_ss = params["wage_hire_ss"]
    wage_hire_aw = params["wage_hire_aw"]
    cow_investment = params["cow_investment"]
    chicken_investment = params["chicken_investment"]
    land_per_cow = params["land_per_cow"]
    labor_cow_aw = params["labor_cow_aw"]
    labor_cow_ss = params["labor_cow_ss"]
    income_cow = params["income_cow"]
    labor_chicken_aw = params["labor_chicken_aw"]
    labor_chicken_ss = params["labor_chicken_ss"]
    income_chicken = params["income_chicken"]
    chicken_coop_capacity = params["chicken_coop_capacity"]
    cowshed_capacity = params["cowshed_capacity"]
    labor_soybean_aw = params["labor_soybean_aw"]
    labor_soybean_ss = params["labor_soybean_ss"]
    income_soybean = params["income_soybean"]
    labor_corn_aw = params["labor_corn_aw"]
    labor_corn_ss = params["labor_corn_ss"]
    income_corn = params["income_corn"]
    labor_wheat_aw = params["labor_wheat_aw"]
    labor_wheat_ss = params["labor_wheat_ss"]
    income_wheat = params["income_wheat"]

    model = gp.Model("farm_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # Crop areas (hectares)
    x_soy = model.addVar(lb=0.0, name="x_soy")    # soybeans
    x_corn = model.addVar(lb=0.0, name="x_corn")   # corn
    x_wheat = model.addVar(lb=0.0, name="x_wheat")  # wheat

    # Number of animals
    x_cow = model.addVar(lb=0.0, name="x_cow")       # cows
    x_chk = model.addVar(lb=0.0, name="x_chk")       # chickens

    # Idle labor that works outside (can earn wages)
    # (outside work earns wages, which adds to income)
    idle_aw = model.addVar(lb=0.0, name="idle_aw")  # unused AW labor (person-days)
    idle_ss = model.addVar(lb=0.0, name="idle_ss")  # unused SS labor (person-days)

    # Land constraint: crop land + cow-grass land <= total land
    model.addConstr(
        x_soy + x_corn + x_wheat + land_per_cow * x_cow <= land_capacity,
        name="land"
    )

    # Capital budget constraint
    model.addConstr(
        cow_investment * x_cow + chicken_investment * x_chk <= capital_budget,
        name="capital"
    )

    # Autumn-winter labor constraint
    # farm labor used + idle labor = total labor capacity
    model.addConstr(
        labor_soybean_aw * x_soy
        + labor_corn_aw * x_corn
        + labor_wheat_aw * x_wheat
        + labor_cow_aw * x_cow
        + labor_chicken_aw * x_chk
        + idle_aw == labor_aw_capacity,
        name="labor_aw"
    )

    # Spring-summer labor constraint
    model.addConstr(
        labor_soybean_ss * x_soy
        + labor_corn_ss * x_corn
        + labor_wheat_ss * x_wheat
        + labor_cow_ss * x_cow
        + labor_chicken_ss * x_chk
        + idle_ss == labor_ss_capacity,
        name="labor_ss"
    )

    # Capacity constraints
    model.addConstr(x_chk <= chicken_coop_capacity, name="coop_cap")
    model.addConstr(x_cow <= cowshed_capacity, name="shed_cap")

    # Objective: maximize net income
    # = income from crops + income from animals + wages from idle labor working outside
    model.setObjective(
        income_soybean * x_soy
        + income_corn * x_corn
        + income_wheat * x_wheat
        + income_cow * x_cow
        + income_chicken * x_chk
        + wage_hire_aw * idle_aw
        + wage_hire_ss * idle_ss,
        GRB.MAXIMIZE
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
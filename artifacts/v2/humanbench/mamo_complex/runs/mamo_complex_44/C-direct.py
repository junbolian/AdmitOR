import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assembly_hours_type1 = params["assembly_hours_type1"]
    testing_hours_type1 = params["testing_hours_type1"]
    materials_cost_type1 = params["materials_cost_type1"]
    assembly_hours_type2 = params["assembly_hours_type2"]
    testing_hours_type2 = params["testing_hours_type2"]
    materials_cost_type2 = params["materials_cost_type2"]
    regular_assembly_capacity = params["regular_assembly_capacity"]
    testing_capacity = params["testing_capacity"]
    overtime_assembly_capacity = params["overtime_assembly_capacity"]
    overtime_cost_per_hour = params["overtime_cost_per_hour"]
    market_value_type1 = params["market_value_type1"]
    market_value_type2 = params["market_value_type2"]

    model = gp.Model("production_profit")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x1 = model.addVar(lb=0.0, name="x1")  # units of product type 1
    x2 = model.addVar(lb=0.0, name="x2")  # units of product type 2
    ot = model.addVar(lb=0.0, ub=overtime_assembly_capacity, name="overtime")  # overtime hours used

    # Objective: maximize profit = revenue - material costs - overtime cost
    revenue = market_value_type1 * x1 + market_value_type2 * x2
    material_cost = materials_cost_type1 * x1 + materials_cost_type2 * x2
    overtime_total_cost = overtime_cost_per_hour * ot

    model.setObjective(revenue - material_cost - overtime_total_cost, GRB.MAXIMIZE)

    # Assembly constraint: regular + overtime hours
    model.addConstr(
        assembly_hours_type1 * x1 + assembly_hours_type2 * x2 <= regular_assembly_capacity + ot,
        name="assembly"
    )

    # Testing constraint
    model.addConstr(
        testing_hours_type1 * x1 + testing_hours_type2 * x2 <= testing_capacity,
        name="testing"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
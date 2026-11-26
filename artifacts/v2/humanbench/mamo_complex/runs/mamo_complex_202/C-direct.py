import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assembly_hours_type1 = params["assembly_hours_type1"]
    testing_hours_type1 = params["testing_hours_type1"]
    material_cost_type1 = params["material_cost_type1"]
    assembly_hours_type2 = params["assembly_hours_type2"]
    testing_hours_type2 = params["testing_hours_type2"]
    material_cost_type2 = params["material_cost_type2"]
    assembly_capacity = params["assembly_capacity"]
    testing_capacity = params["testing_capacity"]
    overtime_max = params["overtime_max"]
    overtime_cost_per_hour = params["overtime_cost_per_hour"]
    price_type1 = params["price_type1"]
    price_type2 = params["price_type2"]

    model = gp.Model("production")
    model.setParam("OutputFlag", 0)

    x1 = model.addVar(lb=0, name="x1")  # units of product type 1
    x2 = model.addVar(lb=0, name="x2")  # units of product type 2
    overtime = model.addVar(lb=0, ub=overtime_max, name="overtime")  # overtime hours

    # Assembly constraint: regular + overtime
    model.addConstr(
        assembly_hours_type1 * x1 + assembly_hours_type2 * x2 <= assembly_capacity + overtime,
        name="assembly"
    )

    # Testing constraint
    model.addConstr(
        testing_hours_type1 * x1 + testing_hours_type2 * x2 <= testing_capacity,
        name="testing"
    )

    # Profit = revenue - material costs - overtime costs
    profit = (
        (price_type1 - material_cost_type1) * x1
        + (price_type2 - material_cost_type2) * x2
        - overtime_cost_per_hour * overtime
    )

    model.setObjective(profit, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
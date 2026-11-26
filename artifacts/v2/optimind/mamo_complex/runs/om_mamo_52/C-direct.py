import gurobipy as gp
from gurobipy import GRB

def solve(params):
    assembly_hours_product1 = params["assembly_hours_product1"]
    testing_hours_product1 = params["testing_hours_product1"]
    material_cost_product1 = params["material_cost_product1"]
    assembly_hours_product2 = params["assembly_hours_product2"]
    testing_hours_product2 = params["testing_hours_product2"]
    material_cost_product2 = params["material_cost_product2"]
    regular_assembly_capacity = params["regular_assembly_capacity"]
    testing_capacity = params["testing_capacity"]
    overtime_assembly_capacity = params["overtime_assembly_capacity"]
    overtime_cost_per_hour = params["overtime_cost_per_hour"]
    market_value_product1 = params["market_value_product1"]
    market_value_product2 = params["market_value_product2"]

    model = gp.Model("production_profit")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x1 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x1")  # units of product 1
    x2 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x2")  # units of product 2
    ot = model.addVar(lb=0, ub=overtime_assembly_capacity, vtype=GRB.CONTINUOUS, name="overtime_hours")

    # Objective: maximize profit = revenue - material costs - overtime costs
    profit = (
        market_value_product1 * x1
        + market_value_product2 * x2
        - material_cost_product1 * x1
        - material_cost_product2 * x2
        - overtime_cost_per_hour * ot
    )
    model.setObjective(profit, GRB.MAXIMIZE)

    # Assembly constraint: regular + overtime hours
    model.addConstr(
        assembly_hours_product1 * x1 + assembly_hours_product2 * x2 <= regular_assembly_capacity + ot,
        name="assembly"
    )

    # Testing constraint
    model.addConstr(
        testing_hours_product1 * x1 + testing_hours_product2 * x2 <= testing_capacity,
        name="testing"
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
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    labor_per_unit_shirt = params["labor_per_unit_shirt"]
    labor_per_unit_short_sleeve = params["labor_per_unit_short_sleeve"]
    labor_per_unit_casual = params["labor_per_unit_casual"]
    material_per_unit_shirt = params["material_per_unit_shirt"]
    material_per_unit_short_sleeve = params["material_per_unit_short_sleeve"]
    material_per_unit_casual = params["material_per_unit_casual"]
    price_shirt = params["price_shirt"]
    price_short_sleeve = params["price_short_sleeve"]
    price_casual = params["price_casual"]
    variable_cost_shirt = params["variable_cost_shirt"]
    variable_cost_short_sleeve = params["variable_cost_short_sleeve"]
    variable_cost_casual = params["variable_cost_casual"]
    labor_capacity = params["labor_capacity"]
    material_capacity = params["material_capacity"]
    fixed_cost_shirt = params["fixed_cost_shirt"]
    fixed_cost_short_sleeve = params["fixed_cost_short_sleeve"]
    fixed_cost_casual = params["fixed_cost_casual"]

    margin_shirt = price_shirt - variable_cost_shirt
    margin_short_sleeve = price_short_sleeve - variable_cost_short_sleeve
    margin_casual = price_casual - variable_cost_casual

    model = gp.Model("RedBeanClothing")
    model.setParam("OutputFlag", 0)

    # Continuous production quantities
    x_shirt = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x_shirt")
    x_short_sleeve = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x_short_sleeve")
    x_casual = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x_casual")

    # Binary variables: 1 if production line is active (incurs fixed cost)
    y_shirt = model.addVar(vtype=GRB.BINARY, name="y_shirt")
    y_short_sleeve = model.addVar(vtype=GRB.BINARY, name="y_short_sleeve")
    y_casual = model.addVar(vtype=GRB.BINARY, name="y_casual")

    # Objective: maximize total profit (revenue - variable costs - fixed costs)
    model.setObjective(
        margin_shirt * x_shirt
        + margin_short_sleeve * x_short_sleeve
        + margin_casual * x_casual
        - fixed_cost_shirt * y_shirt
        - fixed_cost_short_sleeve * y_short_sleeve
        - fixed_cost_casual * y_casual,
        GRB.MAXIMIZE
    )

    # Labor capacity constraint
    model.addConstr(
        labor_per_unit_shirt * x_shirt
        + labor_per_unit_short_sleeve * x_short_sleeve
        + labor_per_unit_casual * x_casual
        <= labor_capacity,
        name="labor"
    )

    # Material capacity constraint
    model.addConstr(
        material_per_unit_shirt * x_shirt
        + material_per_unit_short_sleeve * x_short_sleeve
        + material_per_unit_casual * x_casual
        <= material_capacity,
        name="material"
    )

    # Big-M linking constraints: production only if line is open
    # Upper bound on each product derived from binding constraints
    big_m_shirt = max(labor_capacity / labor_per_unit_shirt, material_capacity / material_per_unit_shirt)
    big_m_short_sleeve = max(labor_capacity / labor_per_unit_short_sleeve, material_capacity / material_per_unit_short_sleeve)
    big_m_casual = max(labor_capacity / labor_per_unit_casual, material_capacity / material_per_unit_casual)

    model.addConstr(x_shirt <= big_m_shirt * y_shirt, name="link_shirt")
    model.addConstr(x_short_sleeve <= big_m_short_sleeve * y_short_sleeve, name="link_short_sleeve")
    model.addConstr(x_casual <= big_m_casual * y_casual, name="link_casual")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
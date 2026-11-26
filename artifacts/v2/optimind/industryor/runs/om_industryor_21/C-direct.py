def solve(params):
    import gurobipy as gp
    from gurobipy import GRB

    # Read parameters
    labor_per_unit = params["labor_per_unit"]          # list of 3
    material_per_unit = params["material_per_unit"]    # list of 3
    selling_price = params["selling_price"]            # list of 3
    variable_cost = params["variable_cost"]            # list of 3
    labor_capacity = params["labor_capacity"]
    material_capacity = params["material_capacity"]
    fixed_cost_shirt = params["fixed_cost_shirt"]
    fixed_cost_short_sleeve = params["fixed_cost_short_sleeve"]
    fixed_cost_casual_cloth = params["fixed_cost_casual_cloth"]

    fixed_costs = [fixed_cost_shirt, fixed_cost_short_sleeve, fixed_cost_casual_cloth]
    products = range(3)

    # Contribution margin per unit (selling price - variable cost)
    margin = [selling_price[i] - variable_cost[i] for i in products]

    model = gp.Model("hongdou_clothing")
    model.setParam("OutputFlag", 0)

    # Continuous production quantities
    x = model.addVars(3, lb=0.0, name="x")

    # Binary: 1 if product i is produced (equipment activated), 0 otherwise
    y = model.addVars(3, vtype=GRB.BINARY, name="y")

    # Objective: maximize total profit = sum of margin*x - sum of fixed_cost*y
    model.setObjective(
        gp.quicksum(margin[i] * x[i] for i in products)
        - gp.quicksum(fixed_costs[i] * y[i] for i in products),
        GRB.MAXIMIZE
    )

    # Labor capacity constraint
    model.addConstr(
        gp.quicksum(labor_per_unit[i] * x[i] for i in products) <= labor_capacity,
        name="labor"
    )

    # Material capacity constraint
    model.addConstr(
        gp.quicksum(material_per_unit[i] * x[i] for i in products) <= material_capacity,
        name="material"
    )

    # Big-M linking constraints: x[i] > 0 only if y[i] = 1
    # Upper bound on x[i]: limited by both labor and material
    for i in products:
        big_m = min(
            labor_capacity / labor_per_unit[i],
            material_capacity / material_per_unit[i]
        )
        model.addConstr(x[i] <= big_m * y[i], name=f"link_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
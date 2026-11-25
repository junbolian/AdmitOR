import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit_per_period = params["holding_cost_per_unit_per_period"]
    machine_hours_grinder = params["machine_hours_grinder"]
    machine_hours_drill = params["machine_hours_drill"]
    machine_hours_borer = params["machine_hours_borer"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    products = range(3)
    periods = range(4)

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    production = model.addVars(products, periods, lb=0, vtype=GRB.CONTINUOUS, name="production")
    inventory = model.addVars(products, periods, lb=0, ub=inventory_limit, vtype=GRB.CONTINUOUS, name="inventory")
    sales = model.addVars(products, periods, lb=0, vtype=GRB.CONTINUOUS, name="sales")

    # Objective: profit from sales minus holding cost on end-of-period inventory
    obj = gp.LinExpr()
    for p in products:
        for t in periods:
            obj += profit_per_unit[p] * sales[p, t]
            obj -= holding_cost_per_unit_per_period * inventory[p, t]
    model.setObjective(obj, GRB.MAXIMIZE)

    # Inventory balance: period 0 has no carry-in
    for p in products:
        model.addConstr(production[p, 0] == sales[p, 0] + inventory[p, 0])
        for t in range(1, 4):
            model.addConstr(inventory[p, t - 1] + production[p, t] == sales[p, t] + inventory[p, t])

    # Sales upper bounds (rows = periods, columns = products)
    for p in products:
        for t in periods:
            model.addConstr(sales[p, t] <= sales_limit[t][p])

    # Required ending inventory at end of period 3
    for p in products:
        model.addConstr(inventory[p, 3] == target_inventory[p])

    # Machine capacity per period
    for t in periods:
        model.addConstr(
            gp.quicksum(machine_hours_grinder[p] * production[p, t] for p in products) <= grinder_capacity[t]
        )
        model.addConstr(
            gp.quicksum(machine_hours_drill[p] * production[p, t] for p in products) <= drill_capacity[t]
        )
        model.addConstr(
            gp.quicksum(machine_hours_borer[p] * production[p, t] for p in products) <= borer_capacity[t]
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}
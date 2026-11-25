import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    machine_capacity = params["machine_capacity"]
    processing_time = params["processing_time"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    target_final_inventory = params["target_final_inventory"]

    num_products = 3
    num_periods = 4
    num_machines = 3

    products = range(num_products)
    periods = range(num_periods)
    machines = range(num_machines)

    def get_val(data, *indices):
        """Flexibly index into scalar, 1D, or 2D data."""
        result = data
        for idx in indices:
            try:
                result = result[idx]
            except (TypeError, KeyError):
                # data is a scalar, ignore remaining indices
                return result
        return result

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sell = model.addVars(products, periods, lb=0.0, name="sell")

    # Objective: maximize profit - holding costs
    revenue = gp.quicksum(
        get_val(profit_per_unit, p) * sell[p, t]
        for p in products for t in periods
    )
    holding = gp.quicksum(
        get_val(holding_cost) * inventory[p, t]
        for p in products for t in periods
    )
    model.setObjective(revenue - holding, GRB.MAXIMIZE)

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_{p}_{t}"
                )
            else:
                model.addConstr(
                    inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_{p}_{t}"
                )

    # Machine capacity constraints
    for mach in machines:
        for t in periods:
            model.addConstr(
                gp.quicksum(
                    get_val(processing_time, mach, p) * produce[p, t]
                    for p in products
                ) <= get_val(machine_capacity, mach, t),
                name=f"machine_{mach}_{t}"
            )

    # Inventory upper bound constraints
    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= get_val(max_inventory, p, t),
                name=f"max_inv_{p}_{t}"
            )

    # Sales upper bound constraints
    for p in products:
        for t in periods:
            model.addConstr(
                sell[p, t] <= get_val(max_sales, p, t),
                name=f"max_sales_{p}_{t}"
            )

    # Target final inventory constraints
    for p in products:
        model.addConstr(
            inventory[p, num_periods - 1] == get_val(target_final_inventory, p),
            name=f"target_inv_{p}"
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
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_capacity = params["machine_capacity"]
    machine_time_req = params["machine_time_req"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]
    borer_downtime_period = params["borer_downtime_period"]

    products = ["product_0", "product_1", "product_2", "product_3"]
    machines = ["grinder", "drill", "borer"]
    periods = list(range(6))

    # Helper to index any sequence/mapping by product name or integer index
    def get_by_product(container, product):
        if isinstance(container, dict):
            return container[product]
        else:
            # list indexed by product order
            return container[products.index(product)]

    def get_sales_limit(product, period):
        sl = sales_limit
        if isinstance(sl, dict):
            val = sl[product]
        else:
            val = sl[products.index(product)]
        if isinstance(val, dict):
            return val[period]
        else:
            return val[period]

    def get_machine_time(machine, product):
        mtr = machine_time_req
        if isinstance(mtr, dict):
            row = mtr[machine]
        else:
            row = mtr[machines.index(machine)]
        if isinstance(row, dict):
            return row[product]
        else:
            return row[products.index(product)]

    def get_machine_capacity(machine):
        mc = machine_capacity
        if isinstance(mc, dict):
            return mc[machine]
        else:
            return mc[machines.index(machine)]

    def get_inventory_limit(product):
        il = inventory_limit
        if isinstance(il, dict):
            return il[product]
        elif hasattr(il, '__len__'):
            return il[products.index(product)]
        else:
            return il

    def get_target_inventory(product):
        ti = target_inventory
        if isinstance(ti, dict):
            return ti[product]
        else:
            return ti[products.index(product)]

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sell = model.addVars(products, periods, lb=0.0, name="sell")

    model.setObjective(
        gp.quicksum(
            get_by_product(profit_per_unit, p) * sell[p, t]
            for p in products for t in periods
        )
        - gp.quicksum(
            holding_cost * inventory[p, t]
            for p in products for t in periods
        ),
        GRB.MAXIMIZE
    )

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

    for mach in machines:
        for t in periods:
            if mach == "borer" and t == borer_downtime_period:
                cap = 0.0
            else:
                cap = get_machine_capacity(mach)
            model.addConstr(
                gp.quicksum(get_machine_time(mach, p) * produce[p, t] for p in products)
                <= cap,
                name=f"capacity_{mach}_{t}"
            )

    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= get_inventory_limit(p),
                name=f"inv_limit_{p}_{t}"
            )

    for p in products:
        for t in periods:
            model.addConstr(
                sell[p, t] <= get_sales_limit(p, t),
                name=f"sales_limit_{p}_{t}"
            )

    for p in products:
        model.addConstr(
            inventory[p, periods[-1]] == get_target_inventory(p),
            name=f"target_inv_{p}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
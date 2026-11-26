import gurobipy as gp
from gurobipy import GRB

def solve(params):
    machine_hours_available = params["machine_hours_available"]
    machine_hours_per_unit_product1 = params["machine_hours_per_unit_product1"]
    machine_hours_per_unit_product2 = params["machine_hours_per_unit_product2"]
    production_cost_product1 = params["production_cost_product1"]
    production_cost_product2 = params["production_cost_product2"]
    selling_price_product1 = params["selling_price_product1"]
    selling_price_product2 = params["selling_price_product2"]
    cash_available = params["cash_available"]
    finance_fraction_product1 = params["finance_fraction_product1"]
    finance_fraction_product2 = params["finance_fraction_product2"]
    extra_machine_hours = params["extra_machine_hours"]
    repair_cost = params["repair_cost"]

    model = gp.Model("max_net_income")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x1 = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x1")  # units of product 1
    x2 = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x2")  # units of product 2
    y = model.addVar(vtype=GRB.BINARY, name="y")                 # 1 if repairs are done

    # Net income = revenue - production costs - repair costs
    revenue1 = selling_price_product1 * x1
    revenue2 = selling_price_product2 * x2
    net_income = (revenue1 + revenue2
                  - production_cost_product1 * x1
                  - production_cost_product2 * x2
                  - repair_cost * y)

    model.setObjective(net_income, GRB.MAXIMIZE)

    # Machine capacity constraint (with optional expansion)
    model.addConstr(
        machine_hours_per_unit_product1 * x1 + machine_hours_per_unit_product2 * x2
        <= machine_hours_available + extra_machine_hours * y,
        name="machine_capacity"
    )

    # Cash availability constraint:
    # Production costs must be covered by available cash plus financed revenue
    model.addConstr(
        production_cost_product1 * x1 + production_cost_product2 * x2
        <= cash_available
          + finance_fraction_product1 * selling_price_product1 * x1
          + finance_fraction_product2 * selling_price_product2 * x2,
        name="cash_availability"
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
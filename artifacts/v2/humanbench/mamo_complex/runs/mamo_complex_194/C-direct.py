import gurobipy as gp
from gurobipy import GRB

def solve(params):
    mh1 = params["machine_hours_per_unit_p1"]
    mh2 = params["machine_hours_per_unit_p2"]
    mh_avail = params["machine_hours_available"]
    cost1 = params["production_cost_p1"]
    cost2 = params["production_cost_p2"]
    price1 = params["selling_price_p1"]
    price2 = params["selling_price_p2"]
    cash = params["available_cash"]
    adv1 = params["revenue_advance_rate_p1"]
    adv2 = params["revenue_advance_rate_p2"]
    extra_mh = params["extra_machine_hours"]
    repair_cost = params["repair_cost"]

    # We decide whether to do repairs (binary) and how much to produce.
    # Net income = revenue - production costs - repair costs
    # revenue - cost = (price - cost) * units, then subtract repair if done.

    model = gp.Model("production_repair")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x1 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x1")  # units of product 1
    x2 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x2")  # units of product 2
    y  = model.addVar(vtype=GRB.BINARY, name="y")              # 1 if repairs done

    # Objective: maximize net income
    # Net income = (price1 - cost1)*x1 + (price2 - cost2)*x2 - repair_cost * y
    model.setObjective(
        (price1 - cost1) * x1 + (price2 - cost2) * x2 - repair_cost * y,
        GRB.MAXIMIZE
    )

    # Machine hours constraint: total used <= available + extra * y
    model.addConstr(mh1 * x1 + mh2 * x2 <= mh_avail + extra_mh * y, name="machine_hours")

    # Cash constraint: production costs <= available cash + advance on revenues
    # cash + adv1 * price1 * x1 + adv2 * price2 * x2 >= cost1 * x1 + cost2 * x2
    # => (cost1 - adv1*price1)*x1 + (cost2 - adv2*price2)*x2 <= cash
    model.addConstr(
        (cost1 - adv1 * price1) * x1 + (cost2 - adv2 * price2) * x2 <= cash,
        name="cash"
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
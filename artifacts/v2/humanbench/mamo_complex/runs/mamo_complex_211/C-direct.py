import gurobipy as gp
from gurobipy import GRB


def solve(params):
    lcR = params["labor_cost_recorder"]
    lcr = params["labor_cost_radio"]
    mcR = params["material_cost_recorder"]
    mcr = params["material_cost_radio"]
    pR  = params["price_recorder"]
    pr  = params["price_radio"]
    capR = params["raw_material_capacity_recorder"]
    capr = params["raw_material_capacity_radio"]
    cash0  = params["cash_initial"]
    ar0    = params["accounts_receivable_initial"]
    inv0   = params["inventory_initial"]
    loan0  = params["loan_liability"]
    arCol  = params["ar_collection_december"]
    loanPay = params["loan_payment_december"]
    rent   = params["rent_december"]
    newMat = params["new_material_january"]
    minCash  = params["min_cash_january"]
    minRatio = params["min_current_ratio"]

    model = gp.Model("semicond")
    model.setParam("OutputFlag", 0)

    R = model.addVar(lb=0.0, ub=capR, vtype=GRB.CONTINUOUS, name="recorders")
    r = model.addVar(lb=0.0, ub=capr, vtype=GRB.CONTINUOUS, name="radios")

    # Profit contribution: revenue minus variable costs
    model.setObjective(
        (pR - lcR - mcR) * R + (pr - lcr - mcr) * r,
        GRB.MAXIMIZE,
    )

    # Cash on January 1:
    # Starting cash + AR collected in Dec - loan payment - rent - labor costs paid in Dec
    cash_jan = cash0 + arCol - loanPay - rent - lcR * R - lcr * r
    model.addConstr(cash_jan >= minCash, "min_cash")

    # January 1 Balance Sheet
    # Current Assets:
    #   cash_jan
    #   AR: original AR minus collected in Dec, plus December credit sales
    ar_jan = ar0 - arCol + pR * R + pr * r
    #   Inventory: original inventory minus raw materials consumed, plus new materials received
    inv_jan = inv0 - mcR * R - mcr * r + newMat
    current_assets = cash_jan + ar_jan + inv_jan

    # Current Liabilities:
    #   Remaining loan + payable for new materials (due Feb 1)
    loan_jan = loan0 - loanPay
    current_liabilities = loan_jan + newMat

    model.addConstr(
        current_assets >= minRatio * current_liabilities,
        "current_ratio",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no optimal solution"}
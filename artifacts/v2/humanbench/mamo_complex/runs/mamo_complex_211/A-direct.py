import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    lc_rec = params["labor_cost_recorder"]
    lc_rad = params["labor_cost_radio"]
    mc_rec = params["material_cost_recorder"]
    mc_rad = params["material_cost_radio"]
    p_rec = params["price_recorder"]
    p_rad = params["price_radio"]
    cap_rec = params["raw_material_capacity_recorder"]
    cap_rad = params["raw_material_capacity_radio"]
    cash0 = params["cash_initial"]
    ar0 = params["accounts_receivable_initial"]
    inv0 = params["inventory_initial"]
    loan0 = params["loan_liability"]
    ar_coll = params["ar_collection_december"]
    loan_pay = params["loan_payment_december"]
    rent = params["rent_december"]
    new_mat = params["new_material_january"]
    min_cash = params["min_cash_january"]
    min_ratio = params["min_current_ratio"]

    model.xr = pyo.Var(within=pyo.NonNegativeReals)
    model.xd = pyo.Var(within=pyo.NonNegativeReals)

    model.material_rec = pyo.Constraint(expr=model.xr <= cap_rec)
    model.material_rad = pyo.Constraint(expr=model.xd <= cap_rad)

    # Cash on Jan 1: initial cash - labor paid in December - loan payment - rent + AR collected
    # Interest not modeled; loan repayment reduces cash.
    cash_jan = cash0 - (lc_rec * model.xr + lc_rad * model.xd) - loan_pay - rent + ar_coll
    model.cash_constraint = pyo.Constraint(expr=cash_jan >= min_cash)

    # Current ratio on Jan 1 >= min_ratio
    # Assets Jan 1: cash + AR + inventory (finished goods at cost = labor+material) + raw materials
    # Liabilities Jan 1: remaining loan + payable for new materials
    remaining_loan = loan0 - loan_pay
    inventory_value = inv0 + (mc_rec + lc_rec) * model.xr + (mc_rad + lc_rad) * model.xd
    assets = cash_jan + ar0 + inventory_value
    liabilities = remaining_loan + new_mat
    model.ratio_constraint = pyo.Constraint(
        expr=assets >= min_ratio * liabilities
    )

    # Objective: contribution to profit from December's production
    model.profit = pyo.Objective(
        expr=(p_rec - lc_rec - mc_rec) * model.xr
        + (p_rad - lc_rad - mc_rad) * model.xd,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}
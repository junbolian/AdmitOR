import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    labor_cost_tape = params["labor_cost_tape"]
    labor_cost_radio = params["labor_cost_radio"]
    material_cost_tape = params["material_cost_tape"]
    material_cost_radio = params["material_cost_radio"]
    price_tape = params["price_tape"]
    price_radio = params["price_radio"]
    raw_material_capacity_tape = params["raw_material_capacity_tape"]
    raw_material_capacity_radio = params["raw_material_capacity_radio"]
    cash_initial = params["cash_initial"]
    accounts_receivable_initial = params["accounts_receivable_initial"]
    inventory_initial = params["inventory_initial"]
    bank_loan_initial = params["bank_loan_initial"]
    ar_collection_december = params["ar_collection_december"]
    loan_repayment_december = params["loan_repayment_december"]
    rent_december = params["rent_december"]
    raw_material_received_january = params["raw_material_received_january"]
    min_cash_january = params["min_cash_january"]
    min_current_ratio_january = params["min_current_ratio_january"]

    # Per-unit contribution (revenue minus labor and material cost)
    contrib_tape = price_tape - labor_cost_tape - material_cost_tape
    contrib_radio = price_radio - labor_cost_radio - material_cost_radio

    model = pyo.ConcreteModel()

    model.x_tape = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_radio = pyo.Var(domain=pyo.NonNegativeReals)

    # Raw material capacity limits
    model.cap_tape = pyo.Constraint(
        expr=model.x_tape <= raw_material_capacity_tape
    )
    model.cap_radio = pyo.Constraint(
        expr=model.x_radio <= raw_material_capacity_radio
    )

    # December cash outflow for production (labor + material paid in December)
    prod_cost = (labor_cost_tape + material_cost_tape) * model.x_tape + (
        labor_cost_radio + material_cost_radio
    ) * model.x_radio

    # December sales revenue (all on credit)
    revenue = price_tape * model.x_tape + price_radio * model.x_radio

    # Cash balance on January 1
    cash_jan = (
        cash_initial
        + ar_collection_december
        - loan_repayment_december
        - rent_december
        - prod_cost
    )

    # Minimum cash balance requirement
    model.cash_req = pyo.Constraint(expr=cash_jan >= min_cash_january)

    # January 1 balance sheet items
    ar_jan = accounts_receivable_initial - ar_collection_december + revenue
    inventory_jan = inventory_initial
    bank_loan_jan = bank_loan_initial - loan_repayment_december
    ap_jan = raw_material_received_january

    # Current ratio >= required
    model.current_ratio = pyo.Constraint(
        expr=(
            cash_jan + ar_jan + inventory_jan
            >= min_current_ratio_january * (bank_loan_jan + ap_jan)
        )
    )

    model.obj = pyo.Objective(
        expr=contrib_tape * model.x_tape + contrib_radio * model.x_radio,
        sense=pyo.maximize,
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
import gurobipy as gp
from gurobipy import GRB

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

    model = gp.Model("semicond")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of tape recorders and radios produced in December
    tape = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="tape")
    radio = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="radio")

    # Objective: maximize contribution to profit
    # Contribution = (price - labor_cost - material_cost) per unit
    contribution_tape = price_tape - labor_cost_tape - material_cost_tape
    contribution_radio = price_radio - labor_cost_radio - material_cost_radio
    model.setObjective(contribution_tape * tape + contribution_radio * radio, GRB.MAXIMIZE)

    # Raw material capacity constraints
    model.addConstr(tape <= raw_material_capacity_tape, name="raw_material_tape")
    model.addConstr(radio <= raw_material_capacity_radio, name="raw_material_radio")

    # Cash on January 1, 2003:
    # Start with cash_initial
    # + ar_collection_december (collected in December)
    # - labor costs paid in December (labor is paid in December)
    # - loan_repayment_december
    # - rent_december
    # Note: raw materials are paid Feb 1, so no December cash outflow for materials
    # Sales are on credit (no cash inflow from December sales until February)
    cash_january = (cash_initial
                    + ar_collection_december
                    - labor_cost_tape * tape
                    - labor_cost_radio * radio
                    - loan_repayment_december
                    - rent_december)

    model.addConstr(cash_january >= min_cash_january, name="min_cash")

    # Current ratio on January 1, 2003:
    # Current assets on Jan 1:
    #   - cash_january
    #   - accounts_receivable on Jan 1:
    #       accounts_receivable_initial
    #       - ar_collection_december (collected in December)
    #       + December sales (price * units, all on credit, collected Feb 1)
    #   - inventory on Jan 1:
    #       inventory_initial
    #       - cost of goods sold (material_cost * units produced and sold)
    #       + raw_material_received_january (new raw materials)
    #   Note: produced units are sold (demand high enough), so inventory of finished goods
    #         The inventory_initial represents Dec 1 inventory.
    #         Goods produced and sold reduce raw material inventory and add to AR.
    #         The raw material cost of produced goods leaves inventory as COGS.
    #         So inventory on Jan 1 = inventory_initial - material_cost_tape*tape - material_cost_radio*radio + raw_material_received_january
    #
    # Current liabilities on Jan 1:
    #   - bank_loan remaining = bank_loan_initial - loan_repayment_december
    #   - accounts payable for raw materials received Jan 1 = raw_material_received_january
    #
    # Current ratio = current_assets / current_liabilities >= min_current_ratio_january

    ar_january = (accounts_receivable_initial
                  - ar_collection_december
                  + price_tape * tape
                  + price_radio * radio)

    inventory_january = (inventory_initial
                         - material_cost_tape * tape
                         - material_cost_radio * radio
                         + raw_material_received_january)

    current_assets_january = cash_january + ar_january + inventory_january

    loan_january = bank_loan_initial - loan_repayment_december
    accounts_payable_january = raw_material_received_january
    current_liabilities_january = loan_january + accounts_payable_january

    # current_assets >= min_current_ratio * current_liabilities
    model.addConstr(
        current_assets_january >= min_current_ratio_january * current_liabilities_january,
        name="current_ratio"
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
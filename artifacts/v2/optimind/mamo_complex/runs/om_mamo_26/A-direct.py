import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    c_raw = params["raw_material_cost_per_lb"]
    lab_proc = params["lab_hours_per_lb_processing"]
    brute_yield = params["brute_oz_per_lb"]
    chan_yield = params["chanelle_oz_per_lb"]
    p_rb = params["regular_brute_price_per_oz"]
    p_rc = params["regular_chanelle_price_per_oz"]
    p_lb = params["luxury_brute_price_per_oz"]
    p_lc = params["luxury_chanelle_price_per_oz"]
    lab_lb = params["luxury_brute_lab_hours_per_oz"]
    lab_lc = params["luxury_chanelle_lab_hours_per_oz"]
    cost_lb = params["luxury_brute_cost_per_oz"]
    cost_lc = params["luxury_chanelle_cost_per_oz"]
    lab_cap = params["lab_hours_capacity"]
    raw_cap = params["raw_material_capacity_lb"]

    # Variables
    model.x = pyo.Var(domain=pyo.NonNegativeReals)  # lbs raw purchased/processed
    model.rb = pyo.Var(domain=pyo.NonNegativeReals)  # oz regular brute sold
    model.rc = pyo.Var(domain=pyo.NonNegativeReals)  # oz regular chanelle sold
    model.lb = pyo.Var(domain=pyo.NonNegativeReals)  # oz luxury brute produced
    model.lc = pyo.Var(domain=pyo.NonNegativeReals)  # oz luxury chanelle produced

    # Regular production available = yield*x; split between selling regular and lux conversion
    model.c1 = pyo.Constraint(expr=model.rb + model.lb == brute_yield * model.x)
    model.c2 = pyo.Constraint(expr=model.rc + model.lc == chan_yield * model.x)

    # Laboratory capacity: processing + luxury conversion
    model.c3 = pyo.Constraint(
        expr=lab_proc * model.x + lab_lb * model.lb + lab_lc * model.lc <= lab_cap
    )

    # Raw material capacity
    model.c4 = pyo.Constraint(expr=model.x <= raw_cap)

    # Objective: maximize profit
    model.profit = pyo.Expression(
        expr=(
            p_rb * model.rb
            + p_rc * model.rc
            + p_lb * model.lb
            + p_lc * model.lc
            - c_raw * model.x
            - cost_lb * model.lb
            - cost_lc * model.lc
        )
    )
    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
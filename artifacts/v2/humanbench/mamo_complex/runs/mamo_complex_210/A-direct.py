import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_cost = params["raw_material_cost_per_lb"]
    lab_per_lb = params["lab_hours_per_lb_raw"]
    rb_yield = params["regular_brute_oz_per_lb"]
    rc_yield = params["regular_chanelle_oz_per_lb"]
    rb_price = params["regular_brute_price_per_oz"]
    rc_price = params["regular_chanelle_price_per_oz"]
    lb_price = params["luxury_brute_price_per_oz"]
    lc_price = params["luxury_chanelle_price_per_oz"]
    rb_further_lab = params["brute_further_lab_hours_per_oz"]
    rc_further_lab = params["chanelle_further_lab_hours_per_oz"]
    rb_further_cost = params["brute_further_cost_per_oz"]
    rc_further_cost = params["chanelle_further_cost_per_oz"]
    lab_cap = params["lab_hours_capacity"]
    raw_cap = params["raw_material_capacity_lb"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.rb_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.rc_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.lb_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.lc_sold = pyo.Var(domain=pyo.NonNegativeReals)

    model.raw_cap_con = pyo.Constraint(expr=model.x <= raw_cap)

    model.brute_balance = pyo.Constraint(
        expr=model.rb_sold + model.lb_sold == rb_yield * model.x
    )
    model.chanelle_balance = pyo.Constraint(
        expr=model.rc_sold + model.lc_sold == rc_yield * model.x
    )

    model.lab_con = pyo.Constraint(
        expr=lab_per_lb * model.x
        + rb_further_lab * model.lb_sold
        + rc_further_lab * model.lc_sold
        <= lab_cap
    )

    model.profit = pyo.Expression(
        expr=rb_price * model.rb_sold
        + rc_price * model.rc_sold
        + lb_price * model.lb_sold
        + lc_price * model.lc_sold
        - rb_further_cost * model.lb_sold
        - rc_further_cost * model.lc_sold
        - raw_cost * model.x
    )

    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
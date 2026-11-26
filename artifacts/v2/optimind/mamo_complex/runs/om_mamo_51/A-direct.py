import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    mh_avail = params["machine_hours_available"]
    h1 = params["machine_hours_per_unit_product1"]
    h2 = params["machine_hours_per_unit_product2"]
    c1 = params["production_cost_product1"]
    c2 = params["production_cost_product2"]
    p1 = params["selling_price_product1"]
    p2 = params["selling_price_product2"]
    cash = params["cash_available"]
    f1 = params["finance_fraction_product1"]
    f2 = params["finance_fraction_product2"]
    extra_mh = params["extra_machine_hours"]
    repair_cost = params["repair_cost"]

    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(within=pyo.NonNegativeReals)
    model.x2 = pyo.Var(within=pyo.NonNegativeReals)
    model.repair = pyo.Var(within=pyo.Binary)

    model.machine_con = pyo.Constraint(
        expr=h1 * model.x1 + h2 * model.x2
        <= mh_avail + extra_mh * model.repair
    )

    model.cash_con = pyo.Constraint(
        expr=c1 * model.x1 + c2 * model.x2 + repair_cost * model.repair
        <= cash + f1 * p1 * model.x1 + f2 * p2 * model.x2
    )

    model.net_income = pyo.Objective(
        expr=(p1 - c1) * model.x1 + (p2 - c2) * model.x2
        - repair_cost * model.repair,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.net_income))
    return {"objective": obj_val, "status": "optimal"}
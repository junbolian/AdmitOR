import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables
    model.x_soybean = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_corn = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_wheat = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_cow = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_chicken = pyo.Var(domain=pyo.NonNegativeReals)
    model.hire_ss = pyo.Var(domain=pyo.NonNegativeReals)
    model.hire_aw = pyo.Var(domain=pyo.NonNegativeReals)

    # Objective: maximize net income
    model.profit = pyo.Expression(
        expr=params["income_soybean"] * model.x_soybean
        + params["income_corn"] * model.x_corn
        + params["income_wheat"] * model.x_wheat
        + params["income_cow"] * model.x_cow
        + params["income_chicken"] * model.x_chicken
        - params["wage_hire_ss"] * model.hire_ss
        - params["wage_hire_aw"] * model.hire_aw
    )
    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    # Land capacity
    model.land_con = pyo.Constraint(
        expr=model.x_soybean
        + model.x_corn
        + model.x_wheat
        + params["land_per_cow"] * model.x_cow
        <= params["land_capacity"]
    )

    # Capital budget
    model.capital_con = pyo.Constraint(
        expr=params["cow_investment"] * model.x_cow
        + params["chicken_investment"] * model.x_chicken
        <= params["capital_budget"]
    )

    # Autumn-winter labor
    model.labor_aw_con = pyo.Constraint(
        expr=params["labor_soybean_aw"] * model.x_soybean
        + params["labor_corn_aw"] * model.x_corn
        + params["labor_wheat_aw"] * model.x_wheat
        + params["labor_cow_aw"] * model.x_cow
        + params["labor_chicken_aw"] * model.x_chicken
        <= params["labor_aw_capacity"] + model.hire_aw
    )

    # Spring-summer labor
    model.labor_ss_con = pyo.Constraint(
        expr=params["labor_soybean_ss"] * model.x_soybean
        + params["labor_corn_ss"] * model.x_corn
        + params["labor_wheat_ss"] * model.x_wheat
        + params["labor_cow_ss"] * model.x_cow
        + params["labor_chicken_ss"] * model.x_chicken
        <= params["labor_ss_capacity"] + model.hire_ss
    )

    # Livestock capacities
    model.cowshed_con = pyo.Constraint(expr=model.x_cow <= params["cowshed_capacity"])
    model.coop_con = pyo.Constraint(expr=model.x_chicken <= params["chicken_coop_capacity"])

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or unsolved: " + type(exc).__name__}

    return {"objective": obj_val, "status": "optimal"}
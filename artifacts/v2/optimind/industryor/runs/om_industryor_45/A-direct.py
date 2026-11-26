import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # -----------------------------
    # Decision variables
    # -----------------------------
    # Animals (can be fractional/continuous)
    model.cow = pyo.Var(domain=pyo.NonNegativeReals,
                        bounds=(0, params["cow_capacity"]))
    model.chicken = pyo.Var(domain=pyo.NonNegativeReals,
                            bounds=(0, params["chicken_capacity"]))

    # Crops (land in hectares)
    model.soybean = pyo.Var(domain=pyo.NonNegativeReals)
    model.corn = pyo.Var(domain=pyo.NonNegativeReals)
    model.wheat = pyo.Var(domain=pyo.NonNegativeReals)

    # External labor (must be full person-days -> integer)
    model.ext_aw = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.ext_ss = pyo.Var(domain=pyo.NonNegativeIntegers)

    # -----------------------------
    # Constraints
    # -----------------------------
    # Land capacity (cows need feed land + crop land)
    model.land_constraint = pyo.Constraint(
        expr=params["cow_land"] * model.cow
             + model.soybean + model.corn + model.wheat
             <= params["land_capacity"]
    )

    # Funds (production development)
    model.funds_constraint = pyo.Constraint(
        expr=params["cow_investment"] * model.cow
             + params["chicken_investment"] * model.chicken
             <= params["funds_capacity"]
    )

    # Labor autumn/winter: used + external = available
    model.labor_aw_constraint = pyo.Constraint(
        expr=params["cow_labor_autumn_winter"] * model.cow
             + params["chicken_labor_autumn_winter"] * model.chicken
             + params["soybean_labor_autumn_winter"] * model.soybean
             + params["corn_labor_autumn_winter"] * model.corn
             + params["wheat_labor_autumn_winter"] * model.wheat
             + model.ext_aw
             <= params["labor_autumn_winter"]
    )

    # Labor spring/summer: used + external = available
    model.labor_ss_constraint = pyo.Constraint(
        expr=params["cow_labor_spring_summer"] * model.cow
             + params["chicken_labor_spring_summer"] * model.chicken
             + params["soybean_labor_spring_summer"] * model.soybean
             + params["corn_labor_spring_summer"] * model.corn
             + params["wheat_labor_spring_summer"] * model.wheat
             + model.ext_ss
             <= params["labor_spring_summer"]
    )

    # -----------------------------
    # Objective: maximize annual net income + external wages
    # -----------------------------
    def obj_rule(m):
        return (
            params["cow_net_income"] * m.cow
            + params["chicken_net_income"] * m.chicken
            + params["soybean_net_income"] * m.soybean
            + params["corn_net_income"] * m.corn
            + params["wheat_net_income"] * m.wheat
            + params["external_wage_spring_summer"] * m.ext_ss
            + params["external_wage_autumn_winter"] * m.ext_aw
        )

    model.total_income = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # -----------------------------
    # Solve
    # -----------------------------
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_income))
    return {'objective': obj_val, 'status': 'optimal'}
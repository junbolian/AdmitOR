# IR: {"sets":{},"params":["land_capacity","funds_capacity","labor_autumn_winter","labor_spring_summer","external_wage_spring_summer","external_wage_autumn_winter","cow_investment","chicken_investment","cow_land","cow_labor_autumn_winter","cow_labor_spring_summer","cow_net_income","chicken_labor_autumn_winter","chicken_labor_spring_summer","chicken_net_income","chicken_capacity","cow_capacity","soybean_labor_autumn_winter","soybean_labor_spring_summer","soybean_net_income","corn_labor_autumn_winter","corn_labor_spring_summer","corn_net_income","wheat_labor_autumn_winter","wheat_labor_spring_summer","wheat_net_income"],"variables":{"soybean_area":"NonNegativeReals","corn_area":"NonNegativeReals","wheat_area":"NonNegativeReals","cows":"NonNegativeIntegers","chickens":"NonNegativeIntegers","external_autumn_winter":"NonNegativeIntegers","external_spring_summer":"NonNegativeIntegers"},"constraints":{"land":"soybean_area + corn_area + wheat_area + cow_land*cows <= land_capacity","funds":"cow_investment*cows + chicken_investment*chickens <= funds_capacity","autumn_winter_labor":"soybean_labor_autumn_winter*soybean_area + corn_labor_autumn_winter*corn_area + wheat_labor_autumn_winter*wheat_area + cow_labor_autumn_winter*cows + chicken_labor_autumn_winter*chickens + external_autumn_winter <= labor_autumn_winter","spring_summer_labor":"soybean_labor_spring_summer*soybean_area + corn_labor_spring_summer*corn_area + wheat_labor_spring_summer*wheat_area + cow_labor_spring_summer*cows + chicken_labor_spring_summer*chickens + external_spring_summer <= labor_spring_summer","cow_limit":"cows <= cow_capacity","chicken_limit":"chickens <= chicken_capacity"},"objective":{"sense":"maximize","expression":"soybean_net_income*soybean_area + corn_net_income*corn_area + wheat_net_income*wheat_area + cow_net_income*cows + chicken_net_income*chickens + external_wage_autumn_winter*external_autumn_winter + external_wage_spring_summer*external_spring_summer"}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    land_capacity = params["land_capacity"]
    funds_capacity = params["funds_capacity"]
    labor_autumn_winter = params["labor_autumn_winter"]
    labor_spring_summer = params["labor_spring_summer"]

    external_wage_spring_summer = params["external_wage_spring_summer"]
    external_wage_autumn_winter = params["external_wage_autumn_winter"]

    cow_investment = params["cow_investment"]
    chicken_investment = params["chicken_investment"]
    cow_land = params["cow_land"]
    cow_labor_autumn_winter = params["cow_labor_autumn_winter"]
    cow_labor_spring_summer = params["cow_labor_spring_summer"]
    cow_net_income = params["cow_net_income"]
    chicken_labor_autumn_winter = params["chicken_labor_autumn_winter"]
    chicken_labor_spring_summer = params["chicken_labor_spring_summer"]
    chicken_net_income = params["chicken_net_income"]
    chicken_capacity = params["chicken_capacity"]
    cow_capacity = params["cow_capacity"]

    soybean_labor_autumn_winter = params["soybean_labor_autumn_winter"]
    soybean_labor_spring_summer = params["soybean_labor_spring_summer"]
    soybean_net_income = params["soybean_net_income"]
    corn_labor_autumn_winter = params["corn_labor_autumn_winter"]
    corn_labor_spring_summer = params["corn_labor_spring_summer"]
    corn_net_income = params["corn_net_income"]
    wheat_labor_autumn_winter = params["wheat_labor_autumn_winter"]
    wheat_labor_spring_summer = params["wheat_labor_spring_summer"]
    wheat_net_income = params["wheat_net_income"]

    model = pyo.ConcreteModel()

    # Annual crop and animal decisions are shared across both seasons.
    model.soybean_area = pyo.Var(domain=pyo.NonNegativeReals)
    model.corn_area = pyo.Var(domain=pyo.NonNegativeReals)
    model.wheat_area = pyo.Var(domain=pyo.NonNegativeReals)

    model.cows = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.chickens = pyo.Var(domain=pyo.NonNegativeIntegers)

    # External employment is measured in whole person-days.
    model.external_autumn_winter = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.external_spring_summer = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.land_limit = pyo.Constraint(
        expr=(
            model.soybean_area
            + model.corn_area
            + model.wheat_area
            + cow_land * model.cows
            <= land_capacity
        )
    )

    model.funds_limit = pyo.Constraint(
        expr=(
            cow_investment * model.cows
            + chicken_investment * model.chickens
            <= funds_capacity
        )
    )

    # Inequalities allow unused fractional labor that cannot be worked externally.
    model.autumn_winter_labor_limit = pyo.Constraint(
        expr=(
            soybean_labor_autumn_winter * model.soybean_area
            + corn_labor_autumn_winter * model.corn_area
            + wheat_labor_autumn_winter * model.wheat_area
            + cow_labor_autumn_winter * model.cows
            + chicken_labor_autumn_winter * model.chickens
            + model.external_autumn_winter
            <= labor_autumn_winter
        )
    )

    model.spring_summer_labor_limit = pyo.Constraint(
        expr=(
            soybean_labor_spring_summer * model.soybean_area
            + corn_labor_spring_summer * model.corn_area
            + wheat_labor_spring_summer * model.wheat_area
            + cow_labor_spring_summer * model.cows
            + chicken_labor_spring_summer * model.chickens
            + model.external_spring_summer
            <= labor_spring_summer
        )
    )

    model.cow_limit = pyo.Constraint(expr=model.cows <= cow_capacity)
    model.chicken_limit = pyo.Constraint(
        expr=model.chickens <= chicken_capacity
    )

    model.total_net_income = pyo.Objective(
        expr=(
            soybean_net_income * model.soybean_area
            + corn_net_income * model.corn_area
            + wheat_net_income * model.wheat_area
            + cow_net_income * model.cows
            + chicken_net_income * model.chickens
            + external_wage_autumn_winter * model.external_autumn_winter
            + external_wage_spring_summer * model.external_spring_summer
        ),
        sense=pyo.maximize,
    )

    # APPsi raises RuntimeError when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    # Objective retrievability is the sole success test.
    try:
        obj_val = float(pyo.value(model.total_net_income))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
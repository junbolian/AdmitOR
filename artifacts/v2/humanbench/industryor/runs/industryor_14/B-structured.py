# IR: {"sets":{"crops":["soybean","corn","wheat"],"animals":["cow","chicken"],"seasons":["aw","ss"],"activities":"crops union animals"},"params":{"land_capacity":"params[land_capacity]","capital_budget":"params[capital_budget]","labor_capacity[aw,ss]":"params[labor_aw_capacity], params[labor_ss_capacity]","wage[aw,ss]":"params[wage_hire_aw], params[wage_hire_ss]","investment[cow,chicken]":"params[cow_investment], params[chicken_investment]","land_per_cow":"params[land_per_cow]","animal_capacity[cow,chicken]":"params[cowshed_capacity], params[chicken_coop_capacity]","labor[activity,season]":"params[labor_<activity>_<season>]","income[activity]":"params[income_<activity>]"},"variables":{"crop_area[crops]":"NonNegativeReals","animal_count[animals]":"NonNegativeIntegers","outside_work[seasons]":"NonNegativeReals","hired_labor[seasons]":"NonNegativeReals"},"constraints":["sum(crop_area) + land_per_cow*animal_count[cow] <= land_capacity","sum(investment[a]*animal_count[a] for a in animals) <= capital_budget","animal_count[a] <= animal_capacity[a] for each animal a","sum(labor[c,s]*crop_area[c] for c in crops) + sum(labor[a,s]*animal_count[a] for a in animals) + outside_work[s] == labor_capacity[s] + hired_labor[s] for each season s"],"objective":"maximize sum(income[c]*crop_area[c] for c in crops) + sum(income[a]*animal_count[a] for a in animals) + sum(wage[s]*(outside_work[s]-hired_labor[s]) for s in seasons)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.crops = pyo.Set(
        initialize=["soybean", "corn", "wheat"], ordered=True
    )
    model.animals = pyo.Set(
        initialize=["cow", "chicken"], ordered=True
    )
    model.seasons = pyo.Set(initialize=["aw", "ss"], ordered=True)
    model.activities = pyo.Set(
        initialize=["soybean", "corn", "wheat", "cow", "chicken"],
        ordered=True,
    )

    model.land_capacity = pyo.Param(
        initialize=params["land_capacity"]
    )
    model.capital_budget = pyo.Param(
        initialize=params["capital_budget"]
    )
    model.land_per_cow = pyo.Param(
        initialize=params["land_per_cow"]
    )

    model.labor_capacity = pyo.Param(
        model.seasons,
        initialize={
            "aw": params["labor_aw_capacity"],
            "ss": params["labor_ss_capacity"],
        },
    )
    model.wage = pyo.Param(
        model.seasons,
        initialize={
            "aw": params["wage_hire_aw"],
            "ss": params["wage_hire_ss"],
        },
    )
    model.investment = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cow_investment"],
            "chicken": params["chicken_investment"],
        },
    )
    model.animal_capacity = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cowshed_capacity"],
            "chicken": params["chicken_coop_capacity"],
        },
    )
    model.labor = pyo.Param(
        model.activities,
        model.seasons,
        initialize={
            ("soybean", "aw"): params["labor_soybean_aw"],
            ("soybean", "ss"): params["labor_soybean_ss"],
            ("corn", "aw"): params["labor_corn_aw"],
            ("corn", "ss"): params["labor_corn_ss"],
            ("wheat", "aw"): params["labor_wheat_aw"],
            ("wheat", "ss"): params["labor_wheat_ss"],
            ("cow", "aw"): params["labor_cow_aw"],
            ("cow", "ss"): params["labor_cow_ss"],
            ("chicken", "aw"): params["labor_chicken_aw"],
            ("chicken", "ss"): params["labor_chicken_ss"],
        },
    )
    model.income = pyo.Param(
        model.activities,
        initialize={
            "soybean": params["income_soybean"],
            "corn": params["income_corn"],
            "wheat": params["income_wheat"],
            "cow": params["income_cow"],
            "chicken": params["income_chicken"],
        },
    )

    model.crop_area = pyo.Var(
        model.crops, domain=pyo.NonNegativeReals
    )
    model.animal_count = pyo.Var(
        model.animals, domain=pyo.NonNegativeIntegers
    )
    model.outside_work = pyo.Var(
        model.seasons, domain=pyo.NonNegativeReals
    )
    model.hired_labor = pyo.Var(
        model.seasons, domain=pyo.NonNegativeReals
    )

    model.land_limit = pyo.Constraint(
        expr=(
            sum(model.crop_area[crop] for crop in model.crops)
            + model.land_per_cow * model.animal_count["cow"]
            <= model.land_capacity
        )
    )
    model.capital_limit = pyo.Constraint(
        expr=(
            sum(
                model.investment[animal] * model.animal_count[animal]
                for animal in model.animals
            )
            <= model.capital_budget
        )
    )

    def animal_capacity_rule(farm, animal):
        return (
            farm.animal_count[animal]
            <= farm.animal_capacity[animal]
        )

    model.housing_limits = pyo.Constraint(
        model.animals, rule=animal_capacity_rule
    )

    def seasonal_labor_rule(farm, season):
        return (
            sum(
                farm.labor[crop, season] * farm.crop_area[crop]
                for crop in farm.crops
            )
            + sum(
                farm.labor[animal, season] * farm.animal_count[animal]
                for animal in farm.animals
            )
            + farm.outside_work[season]
            == farm.labor_capacity[season] + farm.hired_labor[season]
        )

    model.seasonal_labor_balance = pyo.Constraint(
        model.seasons, rule=seasonal_labor_rule
    )

    model.net_income = pyo.Objective(
        expr=(
            sum(
                model.income[crop] * model.crop_area[crop]
                for crop in model.crops
            )
            + sum(
                model.income[animal] * model.animal_count[animal]
                for animal in model.animals
            )
            + sum(
                model.wage[season]
                * (
                    model.outside_work[season]
                    - model.hired_labor[season]
                )
                for season in model.seasons
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this error when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.net_income))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
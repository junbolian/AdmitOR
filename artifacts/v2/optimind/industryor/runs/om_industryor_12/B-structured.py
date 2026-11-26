# IR: {"sets":{"crops":["corn","wheat","soybeans","sorghum"]},"params":["profit_corn","profit_wheat","profit_soybeans","profit_sorghum","total_land","corn_to_wheat_min_ratio","soybean_to_sorghum_min_ratio","wheat_to_sorghum_ratio"],"variables":{"area[crops]":"NonNegativeReals"},"constraints":["sum(area[crop] for crop in crops) <= total_land","area[corn] >= corn_to_wheat_min_ratio * area[wheat]","area[soybeans] >= soybean_to_sorghum_min_ratio * area[sorghum]","area[wheat] == wheat_to_sorghum_ratio * area[sorghum]"],"objective":{"sense":"maximize","expression":"profit_corn*area[corn] + profit_wheat*area[wheat] + profit_soybeans*area[soybeans] + profit_sorghum*area[sorghum]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profits = {
        "corn": params["profit_corn"],
        "wheat": params["profit_wheat"],
        "soybeans": params["profit_soybeans"],
        "sorghum": params["profit_sorghum"],
    }
    total_land = params["total_land"]
    corn_to_wheat_min_ratio = params["corn_to_wheat_min_ratio"]
    soybean_to_sorghum_min_ratio = params["soybean_to_sorghum_min_ratio"]
    wheat_to_sorghum_ratio = params["wheat_to_sorghum_ratio"]

    model = pyo.ConcreteModel()
    model.crops = pyo.Set(
        initialize=["corn", "wheat", "soybeans", "sorghum"],
        ordered=True,
    )
    model.area = pyo.Var(model.crops, domain=pyo.NonNegativeReals)

    model.land_limit = pyo.Constraint(
        expr=sum(model.area[crop] for crop in model.crops) <= total_land
    )
    model.corn_wheat_minimum = pyo.Constraint(
        expr=model.area["corn"]
        >= corn_to_wheat_min_ratio * model.area["wheat"]
    )
    model.soybean_sorghum_minimum = pyo.Constraint(
        expr=model.area["soybeans"]
        >= soybean_to_sorghum_min_ratio * model.area["sorghum"]
    )
    model.wheat_sorghum_equality = pyo.Constraint(
        expr=model.area["wheat"]
        == wheat_to_sorghum_ratio * model.area["sorghum"]
    )

    model.total_profit = pyo.Objective(
        expr=sum(profits[crop] * model.area[crop] for crop in model.crops),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
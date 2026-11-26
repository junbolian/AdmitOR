# IR: {"sets":{"crops":["corn","wheat","soybeans","sorghum"]},"params":["profit_corn","profit_wheat","profit_soybeans","profit_sorghum","total_area","corn_wheat_ratio","soybean_sorghum_ratio","wheat_sorghum_ratio"],"variables":{"area[crops]":"NonNegativeReals"},"constraints":["sum(area[c] for c in crops) <= total_area","area[corn] >= corn_wheat_ratio * area[wheat]","area[soybeans] >= soybean_sorghum_ratio * area[sorghum]","area[wheat] == wheat_sorghum_ratio * area[sorghum]"],"objective":"maximize sum(profit_c * area[c] for c in crops)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    crops = ("corn", "wheat", "soybeans", "sorghum")
    profits = {
        "corn": params["profit_corn"],
        "wheat": params["profit_wheat"],
        "soybeans": params["profit_soybeans"],
        "sorghum": params["profit_sorghum"],
    }
    total_area = params["total_area"]
    corn_wheat_ratio = params["corn_wheat_ratio"]
    soybean_sorghum_ratio = params["soybean_sorghum_ratio"]
    wheat_sorghum_ratio = params["wheat_sorghum_ratio"]

    model = pyo.ConcreteModel()
    model.crops = pyo.Set(initialize=crops, ordered=True)
    model.area = pyo.Var(model.crops, domain=pyo.NonNegativeReals)

    model.land_limit = pyo.Constraint(
        expr=sum(model.area[crop] for crop in model.crops) <= total_area
    )
    model.corn_wheat_requirement = pyo.Constraint(
        expr=model.area["corn"] >= corn_wheat_ratio * model.area["wheat"]
    )
    model.soybean_sorghum_requirement = pyo.Constraint(
        expr=model.area["soybeans"]
        >= soybean_sorghum_ratio * model.area["sorghum"]
    )
    model.wheat_sorghum_requirement = pyo.Constraint(
        expr=model.area["wheat"] == wheat_sorghum_ratio * model.area["sorghum"]
    )

    model.total_profit = pyo.Objective(
        expr=sum(profits[crop] * model.area[crop] for crop in model.crops),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
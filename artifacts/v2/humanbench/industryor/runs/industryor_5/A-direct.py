import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    model = pyo.ConcreteModel()

    model.corn = pyo.Var(domain=pyo.NonNegativeReals)
    model.wheat = pyo.Var(domain=pyo.NonNegativeReals)
    model.soybeans = pyo.Var(domain=pyo.NonNegativeReals)
    model.sorghum = pyo.Var(domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=params["profit_corn"] * model.corn
        + params["profit_wheat"] * model.wheat
        + params["profit_soybeans"] * model.soybeans
        + params["profit_sorghum"] * model.sorghum,
        sense=pyo.maximize,
    )

    model.area_con = pyo.Constraint(
        expr=model.corn + model.wheat + model.soybeans + model.sorghum
        <= params["total_area"]
    )
    model.corn_wheat_con = pyo.Constraint(
        expr=model.corn >= params["corn_wheat_ratio"] * model.wheat
    )
    model.soy_sorghum_con = pyo.Constraint(
        expr=model.soybeans >= params["soybean_sorghum_ratio"] * model.sorghum
    )
    model.wheat_sorghum_con = pyo.Constraint(
        expr=model.wheat == params["wheat_sorghum_ratio"] * model.sorghum
    )

    try:
        result = Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
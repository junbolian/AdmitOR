import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_corn = params["profit_corn"]
    profit_wheat = params["profit_wheat"]
    profit_soybeans = params["profit_soybeans"]
    profit_sorghum = params["profit_sorghum"]
    total_land = params["total_land"]
    corn_to_wheat_min_ratio = params["corn_to_wheat_min_ratio"]
    soybean_to_sorghum_min_ratio = params["soybean_to_sorghum_min_ratio"]
    wheat_to_sorghum_ratio = params["wheat_to_sorghum_ratio"]

    model = pyo.ConcreteModel()

    model.crops = pyo.Set(initialize=["corn", "wheat", "soybeans", "sorghum"])

    model.acres = pyo.Var(model.crops, domain=pyo.NonNegativeReals)

    profits = {
        "corn": profit_corn,
        "wheat": profit_wheat,
        "soybeans": profit_soybeans,
        "sorghum": profit_sorghum,
    }

    def objective_rule(m):
        return sum(profits[c] * m.acres[c] for c in m.crops)

    model.total_profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def land_rule(m):
        return sum(m.acres[c] for c in m.crops) <= total_land

    model.land_limit = pyo.Constraint(rule=land_rule)

    def corn_wheat_rule(m):
        return m.acres["corn"] >= corn_to_wheat_min_ratio * m.acres["wheat"]

    model.corn_wheat = pyo.Constraint(rule=corn_wheat_rule)

    def soy_sorghum_rule(m):
        return m.acres["soybeans"] >= soybean_to_sorghum_min_ratio * m.acres["sorghum"]

    model.soy_sorghum = pyo.Constraint(rule=soy_sorghum_rule)

    def wheat_sorghum_rule(m):
        return m.acres["wheat"] == wheat_to_sorghum_ratio * m.acres["sorghum"]

    model.wheat_sorghum = pyo.Constraint(rule=wheat_sorghum_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}
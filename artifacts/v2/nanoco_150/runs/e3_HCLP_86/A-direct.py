import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_res = 29
    n_sites = 10
    residents = list(range(1, n_res + 1))
    sites = list(range(1, n_sites + 1))

    construction_cost = params["construction_cost"]
    demand_weight = params["demand_weight"]
    premium_benefit = params["premium_benefit"]
    R1 = params["critical_response_threshold_R1"]
    R2 = params["premium_response_threshold_R2"]
    travel_time = params["travel_time"]

    model = pyo.ConcreteModel()

    model.SITES = pyo.Set(initialize=sites)
    model.RES = pyo.Set(initialize=residents)

    model.x = pyo.Var(model.SITES, within=pyo.Binary)

    def crit_cover_rule(m, i):
        return sum(m.x[j] for j in m.SITES if travel_time[i - 1][j - 1] <= R1) >= 1

    model.crit_cover = pyo.Constraint(model.RES, rule=crit_cover_rule)

    model.premium = pyo.Var(model.RES, within=pyo.Binary)

    def premium_rule(m, i):
        return m.premium[i] <= sum(
            m.x[j] for j in m.SITES if travel_time[i - 1][j - 1] <= R2
        )

    model.premium_con = pyo.Constraint(model.RES, rule=premium_rule)

    def obj_rule(m):
        return sum(construction_cost[j - 1] * m.x[j] for j in m.SITES) - sum(
            premium_benefit[i - 1] * m.premium[i] for i in m.RES
        )

    model.net_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.net_cost))
    return {"objective": obj_val, "status": "optimal"}
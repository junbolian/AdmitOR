import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weeks = range(1, 8)
    prods = ["A", "B"]

    demand = {
        "A": {t: params["demand_A"][t - 1] for t in weeks},
        "B": {t: params["demand_B"][t - 1] for t in weeks},
    }
    prod_cost = {
        "A": {t: params["prod_cost_A"][t - 1] for t in weeks},
        "B": {t: params["prod_cost_B"][t - 1] for t in weeks},
    }
    setup_cost = {
        "A": {t: params["setup_cost_A"][t - 1] for t in weeks},
        "B": {t: params["setup_cost_B"][t - 1] for t in weeks},
    }
    hold_cost = {
        "A": {t: params["hold_cost_A"][t - 1] for t in weeks},
        "B": {t: params["hold_cost_B"][t - 1] for t in weeks},
    }
    capacity = {t: params["capacity"][t - 1] for t in weeks}
    res_use = {
        "A": params["resource_use_A"],
        "B": params["resource_use_B"],
    }
    max_prod = {
        "A": {t: params["max_prod_A"][t - 1] for t in weeks},
        "B": {t: params["max_prod_B"][t - 1] for t in weeks},
    }

    model = pyo.ConcreteModel()

    model.WEEKS = pyo.Set(initialize=list(weeks))
    model.PRODS = pyo.Set(initialize=prods)

    model.x = pyo.Var(model.PRODS, model.WEEKS, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.PRODS, model.WEEKS, domain=pyo.NonNegativeReals)
    model.inv0 = pyo.Var(model.PRODS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PRODS, model.WEEKS, domain=pyo.Binary)


    def obj_rule(m):
        total = 0
        for p in prods:
            for t in weeks:
                total += prod_cost[p][t] * m.x[p, t]
                total += setup_cost[p][t] * m.y[p, t]
                total += hold_cost[p][t] * m.inv[p, t]
        return total

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.balance = pyo.ConstraintList()
    for p in prods:
        model.balance.add(
            model.inv0[p] + model.x[p, 1] - model.inv[p, 1] == demand[p][1]
        )
        for t in range(2, 8):
            model.balance.add(
                model.inv[p, t - 1] + model.x[p, t] - model.inv[p, t] == demand[p][t]
            )

    model.capacity_con = pyo.ConstraintList()
    for t in weeks:
        model.capacity_con.add(
            res_use["A"] * model.x["A", t] + res_use["B"] * model.x["B", t]
            <= capacity[t]
        )

    model.setup_link = pyo.ConstraintList()
    for p in prods:
        for t in weeks:
            model.setup_link.add(model.x[p, t] <= max_prod[p][t] * model.y[p, t])

    model.inv0.zero = pyo.Constraint(model.PRODS, rule=lambda m, p: m.inv0[p] == 0)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
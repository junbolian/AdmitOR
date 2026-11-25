import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = range(5)
    products = ["A", "B"]

    prod_cost = {"A": params["prod_cost_A"], "B": params["prod_cost_B"]}
    setup_cost = {"A": params["setup_cost_A"], "B": params["setup_cost_B"]}
    hold_cost = {"A": params["hold_cost_A"], "B": params["hold_cost_B"]}
    cum_demand = {"A": params["demand_A"], "B": params["demand_B"]}
    res_use = {"A": params["resource_use_A"], "B": params["resource_use_B"]}
    max_prod = {"A": params["max_prod_A"], "B": params["max_prod_B"]}
    res_cap = params["resource_capacity"]

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=list(periods))
    model.K = pyo.Set(initialize=products)

    model.prod = pyo.Var(model.K, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.K, model.T, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.K, model.T, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(
            prod_cost[k][t] * model.prod[k, t]
            + setup_cost[k][t] * model.setup[k, t]
            + hold_cost[k][t] * model.inv[k, t]
            for k in model.K
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    model.balance = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda m, k, t: m.inv[k, t]
        == (m.inv[k, t - 1] if t > 0 else 0) + m.prod[k, t],
    )

    model.demand = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda m, k, t: m.inv[k, t] >= cum_demand[k][t],
    )

    model.final_inv = pyo.Constraint(
        model.K,
        rule=lambda m, k: m.inv[k, 4] == cum_demand[k][4],
    )

    model.resource = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(
            res_use[k] * m.prod[k, t] for k in m.K
        )
        <= res_cap[t],
    )

    model.maxprod = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda m, k, t: m.prod[k, t] <= max_prod[k][t],
    )

    model.setup_link = pyo.Constraint(
        model.K,
        model.T,
        rule=lambda m, k, t: m.prod[k, t] <= max_prod[k][t] * m.setup[k, t],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}
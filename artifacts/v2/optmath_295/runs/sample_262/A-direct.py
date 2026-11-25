import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_cost = {
        0: params["shipping_cost_f0"],
        1: params["shipping_cost_f1"],
        2: params["shipping_cost_f2"],
        3: params["shipping_cost_f3"],
    }

    n_fac = 4
    n_cust = 8
    customers = list(range(n_cust))
    facilities = list(range(n_fac))

    model = pyo.ConcreteModel()

    model.fac_open = pyo.Var(facilities, domain=pyo.Binary)
    model.ship = pyo.Var(facilities, customers, domain=pyo.NonNegativeReals)

    model.fixed_term = pyo.Expression(
        expr=sum(fixed_cost[i] * model.fac_open[i] for i in facilities)
    )
    model.ship_term = pyo.Expression(
        expr=sum(
            shipping_cost[i][j] * model.ship[i, j]
            for i in facilities
            for j in customers
        )
    )
    model.total_cost = pyo.Objective(
        expr=model.fixed_term + model.ship_term, sense=pyo.minimize
    )

    model.demand_con = pyo.Constraint(
        customers,
        rule=lambda m, j: sum(m.ship[i, j] for i in facilities) == demand[j],
    )

    model.cap_con = pyo.Constraint(
        facilities,
        rule=lambda m, i: sum(m.ship[i, j] for j in customers)
        <= capacity[i] * m.fac_open[i],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
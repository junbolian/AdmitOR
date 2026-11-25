import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    serving_cost = params["serving_cost"]

    n_fac = 5
    n_cust = 6
    facil = range(n_fac)
    cust = range(n_cust)

    model = pyo.ConcreteModel()

    model.x_fac_open = pyo.Var(facil, domain=pyo.Binary)
    model.y_ship = pyo.Var(facil, cust, domain=pyo.NonNegativeReals)

    model.obj_total_cost = pyo.Objective(
        expr=sum(fixed_cost[i] * model.x_fac_open[i] for i in facil)
        + sum(serving_cost[c][i] * model.y_ship[i, c] for i in facil for c in cust),
        sense=pyo.minimize,
    )

    model.con_demand_sat = pyo.ConstraintList()
    for c in cust:
        model.con_demand_sat.add(
            sum(model.y_ship[i, c] for i in facil) == demand[c]
        )

    model.con_capacity = pyo.ConstraintList()
    for i in facil:
        model.con_capacity.add(
            sum(model.y_ship[i, c] for c in cust) <= capacity[i] * model.x_fac_open[i]
        )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj_total_cost))
    return {"objective": obj_val, "status": "optimal"}
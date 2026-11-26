import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = params["num_facilities"]
    num_customers = params["num_customers"]

    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    facilities = range(num_facilities)
    customers = range(num_customers)

    def tc(i, j):
        try:
            return transport_cost[i][j]
        except (TypeError, IndexError, KeyError):
            pass
        try:
            return transport_cost[i, j]
        except (TypeError, IndexError, KeyError):
            pass
        try:
            return transport_cost[(i, j)]
        except (TypeError, IndexError, KeyError):
            pass
        try:
            return transport_cost[i * num_customers + j]
        except (TypeError, IndexError, KeyError):
            pass
        try:
            return transport_cost[j * num_facilities + i]
        except (TypeError, IndexError, KeyError):
            pass
        return 0.0

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(facilities))
    model.C = pyo.Set(initialize=list(customers))

    model.x = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.F, domain=pyo.Binary)

    model.transport = pyo.Expression(
        expr=sum(tc(i, j) * model.x[i, j] for i in model.F for j in model.C)
    )
    model.opening = pyo.Expression(
        expr=sum(fixed_cost[i] * model.y[i] for i in model.F)
    )
    model.total_cost = pyo.Objective(
        expr=model.transport + model.opening, sense=pyo.minimize
    )

    model.demand_con = pyo.Constraint(
        model.C,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.F) == demand[j],
    )
    model.capacity_con = pyo.Constraint(
        model.F,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in mdl.C) <= capacity[i] * mdl.y[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
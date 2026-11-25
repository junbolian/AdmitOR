import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    num_facilities = int(params["num_facilities"])
    num_customers = int(params["num_customers"])

    F = range(num_facilities)
    C = range(num_customers)

    def tc(i, j):
        # transport_cost may be a nested list/matrix or a flat vector of diagonal entries
        try:
            entry = transport_cost[i][j]
            if isinstance(entry, (list, tuple)):
                return entry[j]
            return entry
        except (TypeError, IndexError):
            pass
        # flat fallback
        try:
            val = transport_cost[i]
            if isinstance(val, (list, tuple)):
                return val[j]
            return val
        except (TypeError, IndexError):
            pass
        # diagonal-only structure: use diagonal entry when i == j, else default
        try:
            diag = transport_cost[i][i]
            if isinstance(diag, (list, tuple)):
                diag = diag[i]
            return diag if i == j else diag
        except (TypeError, IndexError):
            return 0

    model = pyo.ConcreteModel()

    model.x = pyo.Var(F, C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(F, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(fixed_cost[i] * model.y[i] for i in F)
        + sum(tc(i, j) * model.x[i, j] for i in F for j in C),
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        C,
        rule=lambda model, j: sum(model.x[i, j] for i in F) == demand[j],
    )

    model.cap_con = pyo.Constraint(
        F,
        rule=lambda model, i: sum(model.x[i, j] for j in C) <= capacity[i] * model.y[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
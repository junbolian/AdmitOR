# IR: {"sets":{"I":[1,2],"K":[1,2],"J":[1,2]},"params":["a1","a2","b1","b2","f1","f2","q1","q2","c11","c12","c21","c22","c11p","c12p","c21p","c22p"],"variables":{"x[i,k]":"continuous nonnegative; production-to-station flow","z[k,j]":"continuous nonnegative; station-to-demand flow","y[k]":"binary; station activation"},"constraints":["sum(k in K, x[i,k]) <= a[i] for i in I","sum(k in K, z[k,j]) == b[j] for j in J","sum(i in I, x[i,k]) == sum(j in J, z[k,j]) for k in K","sum(i in I, x[i,k]) <= q[k]*y[k] for k in K"],"objective":"minimize sum(i in I,k in K,c[i,k]*x[i,k]) + sum(k in K,j in J,cp[k,j]*z[k,j]) + sum(k in K,f[k]*y[k])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=[1, 2], ordered=True)
    model.K = pyo.Set(initialize=[1, 2], ordered=True)
    model.J = pyo.Set(initialize=[1, 2], ordered=True)

    model.a = pyo.Param(
        model.I,
        initialize={1: params["a1"], 2: params["a2"]},
    )
    model.b = pyo.Param(
        model.J,
        initialize={1: params["b1"], 2: params["b2"]},
    )
    model.f = pyo.Param(
        model.K,
        initialize={1: params["f1"], 2: params["f2"]},
    )
    model.q = pyo.Param(
        model.K,
        initialize={1: params["q1"], 2: params["q2"]},
    )
    model.c = pyo.Param(
        model.I,
        model.K,
        initialize={
            (1, 1): params["c11"],
            (1, 2): params["c12"],
            (2, 1): params["c21"],
            (2, 2): params["c22"],
        },
    )
    model.cp = pyo.Param(
        model.K,
        model.J,
        initialize={
            (1, 1): params["c11p"],
            (1, 2): params["c12p"],
            (2, 1): params["c21p"],
            (2, 2): params["c22p"],
        },
    )

    model.x = pyo.Var(model.I, model.K, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(model.K, model.J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.K, domain=pyo.Binary)

    def supply_rule(instance, i):
        return sum(instance.x[i, k] for k in instance.K) <= instance.a[i]

    model.supply_limit = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(instance, j):
        return sum(instance.z[k, j] for k in instance.K) == instance.b[j]

    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)

    def station_balance_rule(instance, k):
        return (
            sum(instance.x[i, k] for i in instance.I)
            == sum(instance.z[k, j] for j in instance.J)
        )

    model.station_balance = pyo.Constraint(
        model.K, rule=station_balance_rule
    )

    def station_capacity_rule(instance, k):
        return (
            sum(instance.x[i, k] for i in instance.I)
            <= instance.q[k] * instance.y[k]
        )

    model.station_capacity = pyo.Constraint(
        model.K, rule=station_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.c[i, k] * model.x[i, k]
                for i in model.I
                for k in model.K
            )
            + sum(
                model.cp[k, j] * model.z[k, j]
                for k in model.K
                for j in model.J
            )
            + sum(model.f[k] * model.y[k] for k in model.K)
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
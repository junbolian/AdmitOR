import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    model = pyo.ConcreteModel()

    I = [1, 2]
    K = [1, 2]
    J = [1, 2]

    a = {1: params["a1"], 2: params["a2"]}
    b = {1: params["b1"], 2: params["b2"]}
    f = {1: params["f1"], 2: params["f2"]}
    q = {1: params["q1"], 2: params["q2"]}
    c = {(1, 1): params["c11"], (1, 2): params["c12"],
         (2, 1): params["c21"], (2, 2): params["c22"]}
    cp = {(1, 1): params["c11p"], (1, 2): params["c12p"],
          (2, 1): params["c21p"], (2, 2): params["c22p"]}

    model.x = pyo.Var(I, K, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(K, J, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(K, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(c[i, k] * model.x[i, k] for i in I for k in K)
        + sum(cp[k, j] * model.y[k, j] for k in K for j in J)
        + sum(f[k] * model.z[k] for k in K),
        sense=pyo.minimize,
    )

    model.prod_supply = pyo.Constraint(
        I, rule=lambda model, i: sum(model.x[i, k] for k in K) <= a[i]
    )
    model.demand = pyo.Constraint(
        J, rule=lambda model, j: sum(model.y[k, j] for k in K) >= b[j]
    )
    model.flow_balance = pyo.Constraint(
        K, rule=lambda model, k: sum(model.x[i, k] for i in I)
        - sum(model.y[k, j] for j in J) == 0
    )
    model.capacity = pyo.Constraint(
        K, rule=lambda model, k: sum(model.y[k, j] for j in J) <= q[k] * model.z[k]
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}
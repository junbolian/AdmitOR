import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    rel = {
        1: params["reliability_component1"],
        2: params["reliability_component2"],
        3: params["reliability_component3"],
    }
    price = params["unit_price"]
    weight = params["unit_weight"]
    budget = params["total_budget"]
    weight_limit = params["total_weight_limit"]

    components = [1, 2, 3]
    n_spares = list(range(6))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(components, domain=pyo.NonNegativeIntegers, bounds=(0, 5))

    # link each component's spares to exactly one reliability level
    model.z = pyo.Var(components, n_spares, domain=pyo.Binary)
    model.link = pyo.ConstraintList()
    for i in components:
        model.link.add(sum(model.z[i, k] for k in n_spares) == 1)
        model.link.add(model.x[i] == sum(k * model.z[i, k] for k in n_spares))

    model.budget = pyo.Constraint(
        expr=sum(price[i - 1] * model.x[i] for i in components) <= budget
    )
    model.weight_con = pyo.Constraint(
        expr=sum(weight[i - 1] * model.x[i] for i in components) <= weight_limit
    )

    # log-linearized objective: sum of log reliabilities (maximized)
    def log_rel(i, k):
        r = rel[i][k]
        # r is in (0, 1]; use a small floor to avoid log(0)
        if r <= 0:
            r = 1e-12
        return pyo.log(r)

    model.obj = pyo.Objective(
        expr=sum(log_rel(i, k) * model.z[i, k] for i in components for k in n_spares),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    # convert back to actual reliability
    system_rel = float(pyo.exp(obj_val))
    return {"objective": system_rel, "status": "optimal"}
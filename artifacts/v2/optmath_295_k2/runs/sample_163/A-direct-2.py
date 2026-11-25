import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    benefits = params["pairwise_benefits"]
    num_selected = params["num_selected"]

    n = 5
    # Ordered pairs (i, j) with i != j, row-major
    pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    w = {pairs[k]: benefits[k] for k in range(len(pairs))}

    model = pyo.ConcreteModel()
    model.x = pyo.Var(range(n), domain=pyo.Binary)
    model.z = pyo.Var(pairs, domain=pyo.Binary)

    model.card = pyo.Constraint(
        expr=sum(model.x[i] for i in range(n)) == num_selected
    )

    def link_rule(mdl, i, j):
        return mdl.z[i, j] <= mdl.x[i]

    def link_rule2(mdl, i, j):
        return mdl.z[i, j] <= mdl.x[j]

    model.link1 = pyo.Constraint(pairs, rule=link_rule)
    model.link2 = pyo.Constraint(pairs, rule=link_rule2)

    model.obj = pyo.Objective(
        expr=sum(w[i, j] * model.z[i, j] for (i, j) in pairs),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
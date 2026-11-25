import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    weights = params["weights"]
    N = 5

    ordered_pairs = [(i, j) for i in range(N) for j in range(N) if i != j]
    w = {pair: weights[k] for k, pair in enumerate(ordered_pairs)}

    model = pyo.ConcreteModel()
    model.x = pyo.Var(range(N), domain=pyo.Binary)

    # Linearize products x[i]*x[j] with auxiliary binaries y[(i,j)]
    model.y = pyo.Var(ordered_pairs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(w[(i, j)] * mdl.y[(i, j)] for (i, j) in ordered_pairs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.card = pyo.Constraint(expr=sum(model.x[i] for i in range(N)) == 3)

    def link_upper_i(mdl, i, j):
        return mdl.y[(i, j)] <= mdl.x[i]
    model.link_upper_i = pyo.Constraint(ordered_pairs, rule=link_upper_i)

    def link_upper_j(mdl, i, j):
        return mdl.y[(i, j)] <= mdl.x[j]
    model.link_upper_j = pyo.Constraint(ordered_pairs, rule=link_upper_j)

    def link_lower(mdl, i, j):
        return mdl.y[(i, j)] >= mdl.x[i] + mdl.x[j] - 1
    model.link_lower = pyo.Constraint(ordered_pairs, rule=link_lower)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
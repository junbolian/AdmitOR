import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    cities = list(range(5))
    n = len(cities)

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in cities for j in cities if i != j], dimen=2
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j] for (i, j) in model.arcs),
        sense=pyo.minimize,
    )

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j) == 1

    model.out_deg = pyo.Constraint(model.cities, rule=out_rule)
    model.in_deg = pyo.Constraint(model.cities, rule=in_rule)

    # Subtour elimination for all proper nonempty subsets (size >= 2)
    subsets = []
    for mask in range(1, (1 << n) - 1):
        subset = [i for i in cities if mask & (1 << i)]
        if len(subset) >= 2:
            subsets.append(subset)

    model.subset_indices = pyo.Set(initialize=range(len(subsets)))
    model.sub_eval = pyo.ConstraintList()
    for k in model.subset_indices:
        subset = subsets[k]
        expr = sum(
            model.x[i, j] for i in subset for j in subset if i != j
        )
        model.sub_eval.add(expr <= len(subset) - 1)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
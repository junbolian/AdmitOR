import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["E", "F", "G", "H", "I"]

    cost = {
        ("E", "F"): params["cost_E_F"],
        ("E", "G"): params["cost_E_G"],
        ("E", "H"): params["cost_E_H"],
        ("E", "I"): params["cost_E_I"],
        ("F", "G"): params["cost_F_G"],
        ("F", "H"): params["cost_F_H"],
        ("F", "I"): params["cost_F_I"],
        ("G", "H"): params["cost_G_H"],
        ("G", "I"): params["cost_G_I"],
        ("H", "I"): params["cost_H_I"],
    }

    def edge_cost(i, j):
        if i == j:
            return 0.0
        return cost[(i, j)] if (i, j) in cost else cost[(j, i)]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=cities)
    model.ARCS = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(edge_cost(i, j) * model.x[i, j] for (i, j) in model.ARCS),
        sense=pyo.minimize,
    )

    model.out_degree = pyo.Constraint(
        model.NODES,
        rule=lambda model, i: sum(model.x[i, j] for j in cities if j != i) == 1,
    )
    model.in_degree = pyo.Constraint(
        model.NODES,
        rule=lambda model, j: sum(model.x[i, j] for i in cities if i != j) == 1,
    )

    # Subtour elimination (DFJ) for every proper subset of size 2..n-1
    subsets = []
    for mask in range(1, (1 << len(cities)) - 1):
        subset = [cities[k] for k in range(len(cities)) if (mask >> k) & 1]
        if 2 <= len(subset) <= len(cities) - 1:
            subsets.append(subset)

    model.SUBSETS = pyo.Set(initialize=range(len(subsets)))
    model.sec = pyo.Constraint(
        model.SUBSETS,
        rule=lambda model, s: sum(
            model.x[i, j] for i in subsets[s] for j in subsets[s] if i != j
        ) <= len(subsets[s]) - 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
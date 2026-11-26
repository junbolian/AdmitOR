import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ["Alpha", "Bravo", "Charlie", "Delta"]

    cost_dict = {
        ("Alpha", "Bravo"): params["cost_Alpha_Bravo"],
        ("Alpha", "Charlie"): params["cost_Alpha_Charlie"],
        ("Alpha", "Delta"): params["cost_Alpha_Delta"],
        ("Bravo", "Alpha"): params["cost_Bravo_Alpha"],
        ("Bravo", "Charlie"): params["cost_Bravo_Charlie"],
        ("Bravo", "Delta"): params["cost_Bravo_Delta"],
        ("Charlie", "Alpha"): params["cost_Charlie_Alpha"],
        ("Charlie", "Bravo"): params["cost_Charlie_Bravo"],
        ("Charlie", "Delta"): params["cost_Charlie_Delta"],
        ("Delta", "Alpha"): params["cost_Delta_Alpha"],
        ("Delta", "Bravo"): params["cost_Delta_Bravo"],
        ("Delta", "Charlie"): params["cost_Delta_Charlie"],
    }

    arcs = list(cost_dict.keys())

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def objective_rule(mdl):
        return sum(cost_dict[a] * mdl.x[a] for a in arcs)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def out_degree_rule(mdl, c):
        return sum(mdl.x[(c, d)] for d in cities if d != c) == 1

    model.out_degree = pyo.Constraint(cities, rule=out_degree_rule)

    def in_degree_rule(mdl, c):
        return sum(mdl.x[(d, c)] for d in cities if d != c) == 1

    model.in_degree = pyo.Constraint(cities, rule=in_degree_rule)

    subsets = [["Alpha", "Bravo"], ["Alpha", "Charlie"], ["Alpha", "Delta"],
               ["Bravo", "Charlie"], ["Bravo", "Delta"], ["Charlie", "Delta"]]

    def subtour_rule(mdl, k):
        subset = subsets[k]
        internal = [(i, j) for i in subset for j in subset
                    if i != j and (i, j) in cost_dict]
        return sum(mdl.x[a] for a in internal) <= len(subset) - 1

    model.subtour = pyo.Constraint(range(len(subsets)), rule=subtour_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
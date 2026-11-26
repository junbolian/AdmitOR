import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = ["E", "F", "G", "H"]

    cost = {
        ("E", "F"): params["cost_E_to_F"],
        ("E", "G"): params["cost_E_to_G"],
        ("E", "H"): params["cost_E_to_H"],
        ("F", "E"): params["cost_F_to_E"],
        ("F", "G"): params["cost_F_to_G"],
        ("F", "H"): params["cost_F_to_H"],
        ("G", "E"): params["cost_G_to_E"],
        ("G", "F"): params["cost_G_to_F"],
        ("G", "H"): params["cost_G_to_H"],
        ("H", "E"): params["cost_H_to_E"],
        ("H", "F"): params["cost_H_to_F"],
        ("H", "G"): params["cost_H_to_G"],
    }

    arcs = [(i, j) for i in locations for j in locations if i != j]

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each location has exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in locations if j != i) == 1

    model.out_con = pyo.Constraint(locations, rule=out_rule)

    # Each location has exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in locations if i != j) == 1

    model.in_con = pyo.Constraint(locations, rule=in_rule)

    # Subtour elimination for all proper subsets of size 2 and 3
    subsets = [
        ["E", "F"], ["E", "G"], ["E", "H"],
        ["F", "G"], ["F", "H"], ["G", "H"],
        ["E", "F", "G"], ["E", "F", "H"],
        ["E", "G", "H"], ["F", "G", "H"],
    ]

    def sec_rule(mdl, k):
        subset = subsets[k]
        return sum(
            mdl.x[i, j]
            for i in subset
            for j in subset
            if i != j
        ) <= len(subset) - 1

    model.SECS = pyo.Set(initialize=range(len(subsets)))
    model.sec_con = pyo.Constraint(model.SECS, rule=sec_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
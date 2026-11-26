import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]

    travel_cost = {
        (1, 2): params["c12"],
        (1, 3): params["c13"],
        (1, 4): params["c14"],
        (2, 1): params["c21"],
        (2, 3): params["c23"],
        (2, 4): params["c24"],
        (3, 1): params["c31"],
        (3, 2): params["c32"],
        (3, 4): params["c34"],
        (4, 1): params["c41"],
        (4, 2): params["c42"],
        (4, 3): params["c43"],
    }

    arcs = list(travel_cost.keys())

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(travel_cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[(i, j)] for (a, j) in arcs if a == i) == 1

    model.out_cons = pyo.Constraint(cities, rule=out_rule)

    # Each city has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[(i, b)] for (i, b) in arcs if b == j) == 1

    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (DFJ) for all proper non-empty subsets
    # For n=4, subsets of size 2 and 3 suffice (size 1 and 3 are redundant with degree constraints for size 1)
    subsets = [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4],
               [1, 2, 3], [1, 2, 4], [1, 3, 4], [2, 3, 4]]

    def subtour_rule(m, k):
        s = subsets[k]
        s_set = set(s)
        internal = [(i, j) for (i, j) in arcs if i in s_set and j in s_set]
        return sum(m.x[a] for a in internal) <= len(s) - 1

    model.subtour_cons = pyo.Constraint(range(len(subsets)), rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
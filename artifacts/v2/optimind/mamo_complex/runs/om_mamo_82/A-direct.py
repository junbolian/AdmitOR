import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]

    # Read all pairwise costs from params (i != j)
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_{}{}".format(i, j)]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Objective: minimize total travel cost
    model.total_cost = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Each city entered exactly once
    model.in_degree = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1,
    )

    # Each city left exactly once
    model.out_degree = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[(i, j)] for j in cities if i != j) == 1,
    )

    # Subtour elimination (MTZ-style cut for 4-city TSP: forbid 2-city subtours)
    # For a 4-city tour, forbid any proper subset S with 2 <= |S| <= 3 having
    # internal arcs summing to |S| (all internal). Enumerate proper subsets.
    import itertools

    subsets = []
    for size in (2, 3):
        for subset in itertools.combinations(cities, size):
            subsets.append(frozenset(subset))

    def subtour_rule(m, k):
        S = subsets[k]
        internal = [(i, j) for (i, j) in arcs if i in S and j in S]
        # At most |S|-1 arcs within the subset
        return sum(m.x[(i, j)] for (i, j) in internal) <= len(S) - 1

    model.subsets = pyo.RangeSet(0, len(subsets) - 1)
    model.subtour = pyo.Constraint(
        model.subsets,
        rule=lambda m, k: subtour_rule(m, k),
    )

    solver = Highs()
    solver.config.load_solution = True
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
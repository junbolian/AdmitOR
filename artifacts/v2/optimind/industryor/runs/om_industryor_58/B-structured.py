# IR: {"sets":{"V":"{1,...,N}","E":"{(i,j): i,j in V, i<j}","S":"all subsets of V\\{1} with 2<=|S|<=N-1"},"params":{"N":"params['N']","distance_matrix":"params['distance_matrix']; upper-triangular distances in row-major order","d[i,j]":"distance_matrix entry corresponding to (i,j) in E"},"variables":{"x[i,j]":"binary for (i,j) in E"},"constraints":{"degree":"sum(x[min(i,j),max(i,j)] for j in V if j!=i)=2 for every i in V","subtour":"sum(x[i,j] for (i,j) in E if i,j in S)<=|S|-1 for every S"},"objective":"minimize sum(d[i,j]*x[i,j] for (i,j) in E)"}

import operator
from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    customer_count = operator.index(params["N"])
    distances = list(params["distance_matrix"])

    if customer_count < 3:
        raise ValueError("N must be at least 3 for this undirected TSP formulation.")

    locations = list(range(1, customer_count + 1))
    edges = list(combinations(locations, 2))

    if len(distances) != len(edges):
        raise ValueError(
            "distance_matrix must contain N*(N-1)/2 upper-triangular entries."
        )

    edge_distances = dict(zip(edges, distances))

    model = pyo.ConcreteModel()
    model.locations = pyo.Set(initialize=locations, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)
    model.edge_distance = pyo.Param(
        model.edges,
        initialize=edge_distances,
        within=pyo.NonNegativeReals,
    )
    model.route = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(instance, location):
        return sum(
            instance.route[min(location, other), max(location, other)]
            for other in locations
            if other != location
        ) == 2

    model.degree_constraints = pyo.Constraint(
        model.locations, rule=degree_rule
    )

    # Every disconnected cycle would leave a cycle excluding location 1.
    model.subtour_constraints = pyo.ConstraintList()
    nondepot_locations = locations[1:]
    for subset_size in range(2, customer_count):
        for subset in combinations(nondepot_locations, subset_size):
            model.subtour_constraints.add(
                sum(
                    model.route[first, second]
                    for first, second in combinations(subset, 2)
                )
                <= subset_size - 1
            )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.edge_distance[first, second] * model.route[first, second]
            for first, second in edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
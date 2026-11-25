# IR: {"sets":{"V":"{0,...,7}","D":"{0,1}","A":"{(i,j) in V*V: i!=j}","R":"{(0,2),(0,6),(1,3),(1,6),(2,4),(2,7),(3,5),(3,7)}","K":"{1,...,127}","S[k]":"{i in V\\{0}: bit (i-1) of k is set}"},"params":{"coords":"real[V,D], from params['coords']; descriptive geometry","distance_matrix":"nonnegative[A], from params['distance_matrix']; authoritative travel costs"},"variables":{"traversals[i,j]":"nonnegative integer, (i,j) in A"},"constraints":["required_coverage[i,j]: traversals[i,j]+traversals[j,i]>=1 for (i,j) in R","flow_balance[i]: sum(j!=i) traversals[i,j]=sum(j!=i) traversals[j,i] for i in V","depot_connectivity[k]: sum(i in S[k], j in V\\S[k]) traversals[i,j]>=1 for k in K"],"objective":"minimize sum((i,j) in A) distance_matrix[i,j]*traversals[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.vertices = pyo.RangeSet(0, 7)
    model.coordinate_axes = pyo.RangeSet(0, 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )
    model.required_edges = pyo.Set(
        dimen=2,
        initialize=[
            (0, 2),
            (0, 6),
            (1, 3),
            (1, 6),
            (2, 4),
            (2, 7),
            (3, 5),
            (3, 7),
        ],
    )
    model.subset_masks = pyo.RangeSet(1, (1 << 7) - 1)

    model.coords = pyo.Param(
        model.vertices,
        model.coordinate_axes,
        initialize=lambda mdl, i, axis: coords[i][axis],
        within=pyo.Reals,
    )
    model.distance_matrix = pyo.Param(
        model.arcs,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.traversals = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeIntegers,
    )

    def required_coverage_rule(mdl, i, j):
        return mdl.traversals[i, j] + mdl.traversals[j, i] >= 1

    model.required_coverage = pyo.Constraint(
        model.required_edges,
        rule=required_coverage_rule,
    )

    def flow_balance_rule(mdl, i):
        return (
            sum(mdl.traversals[i, j] for j in mdl.vertices if j != i)
            == sum(mdl.traversals[j, i] for j in mdl.vertices if j != i)
        )

    model.flow_balance = pyo.Constraint(
        model.vertices,
        rule=flow_balance_rule,
    )

    def depot_connectivity_rule(mdl, mask):
        subset = {
            i for i in range(1, 8)
            if mask & (1 << (i - 1))
        }
        return sum(
            mdl.traversals[i, j]
            for i in subset
            for j in mdl.vertices
            if j not in subset
        ) >= 1

    # Every vertex is incident to a required edge. These cuts connect all
    # traversed edges to the depot; flow balance then permits one Euler tour.
    model.depot_connectivity = pyo.Constraint(
        model.subset_masks,
        rule=depot_connectivity_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance_matrix[i, j] * model.traversals[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when no feasible solution can load.
        # Leave variables uninitialized and let objective retrieval decide.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
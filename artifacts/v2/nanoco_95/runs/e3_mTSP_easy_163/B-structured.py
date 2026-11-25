# IR: {"sets":{"N":"{0,...,n}","C":"{1,...,n}","D":"{0,1}","A":"{(i,j) in N x N: i != j}","P":"{(i,j) in C x C: i != j}"},"params":{"n":"params['num_clinic_nodes']","K":"params['num_vehicles']","coordinates[i,d]":"params['node_coordinates'][i][d] (metadata)","distance[i,j]":"params['distance_matrix'][i][j]"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,n] for i in C"},"constraints":["Each clinic has exactly one incoming arc: sum(i in N, i != j) x[i,j] = 1 for j in C.","Each clinic has exactly one outgoing arc: sum(j in N, j != i) x[i,j] = 1 for i in C.","Exactly K nonempty routes leave the depot: sum(j in C) x[0,j] = K.","Exactly K routes return to the depot: sum(i in C) x[i,0] = K.","Exclude clinic-only subtours: u[i] - u[j] + n*x[i,j] <= n - 1 for (i,j) in P."],"objective":"minimize sum((i,j) in A) distance[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = params["num_clinic_nodes"]
    vehicle_count = params["num_vehicles"]
    coordinates = params["node_coordinates"]
    distances = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(n + 1), ordered=True)
    model.clinics = pyo.Set(initialize=range(1, n + 1), ordered=True)
    model.dimensions = pyo.Set(initialize=(0, 1), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(n + 1)
            for j in range(n + 1)
            if i != j
        ),
    )
    model.clinic_pairs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(1, n + 1)
            for j in range(1, n + 1)
            if i != j
        ),
    )

    model.clinic_count = pyo.Param(
        initialize=n, within=pyo.NonNegativeIntegers
    )
    model.vehicle_count = pyo.Param(
        initialize=vehicle_count, within=pyo.NonNegativeIntegers
    )
    model.coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize=lambda mdl, i, d: coordinates[i][d],
        within=pyo.Reals,
    )
    model.distance = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda mdl, i, j: distances[i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.clinics,
        domain=pyo.Reals,
        bounds=(1, n),
    )

    def incoming_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.nodes if i != j) == 1

    model.clinic_incoming = pyo.Constraint(
        model.clinics, rule=incoming_rule
    )

    def outgoing_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.nodes if j != i) == 1

    model.clinic_outgoing = pyo.Constraint(
        model.clinics, rule=outgoing_rule
    )

    model.depot_departures = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.clinics)
        == model.vehicle_count
    )
    model.depot_returns = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in model.clinics)
        == model.vehicle_count
    )

    def subtour_rule(mdl, i, j):
        return (
            mdl.u[i] - mdl.u[j] + mdl.clinic_count * mdl.x[i, j]
            <= mdl.clinic_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.clinic_pairs, rule=subtour_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Still determine success solely by objective retrieval below.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"N":"range(num_nodes)","C":"range(1,num_collection_points+1)","A":"{(i,j) in N*N: i!=j}","D":"{0,1}"},"params":{"coordinates":"N*D -> real; descriptive only","distance_matrix":"N*N -> nonnegative real","num_vehicles":"nonnegative integer; fleet cap","num_nodes":"positive integer; total node count","num_collection_points":"positive integer; collection point count"},"variables":{"x[i,j]":"binary, (i,j) in A","u[i]":"continuous in [1,num_collection_points], i in C"},"constraints":["For each j in C: sum(i in N, i!=j) x[i,j] = 1.","For each i in C: sum(j in N, j!=i) x[i,j] = 1.","sum(j in C) x[0,j] = sum(i in C) x[i,0].","sum(j in C) x[0,j] <= num_vehicles.","For distinct i,j in C: u[i]-u[j]+num_collection_points*x[i,j] <= num_collection_points-1."],"objective":"Minimize sum((i,j) in A) distance_matrix[i,j]*x[i,j]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coordinates = params["coordinates"]
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]
    num_nodes = params["num_nodes"]
    num_collection_points = params["num_collection_points"]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.C = pyo.Set(
        initialize=range(1, num_collection_points + 1),
        within=model.N,
        ordered=True,
    )
    model.D = pyo.Set(initialize=(0, 1), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
        ordered=True,
    )

    model.num_nodes = pyo.Param(
        initialize=num_nodes,
        within=pyo.PositiveIntegers,
    )
    model.num_collection_points = pyo.Param(
        initialize=num_collection_points,
        within=pyo.PositiveIntegers,
    )
    model.num_vehicles = pyo.Param(
        initialize=num_vehicles,
        within=pyo.NonNegativeIntegers,
    )
    model.coordinates = pyo.Param(
        model.N,
        model.D,
        initialize=lambda mdl, i, axis: coordinates[i][axis],
        within=pyo.Reals,
    )
    model.distance_matrix = pyo.Param(
        model.N,
        model.N,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, num_collection_points),
    )

    def incoming_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.N if i != j) == 1

    model.unique_incoming = pyo.Constraint(model.C, rule=incoming_rule)

    def outgoing_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.N if j != i) == 1

    model.unique_outgoing = pyo.Constraint(model.C, rule=outgoing_rule)

    model.depot_balance = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.C)
        == sum(model.x[i, 0] for i in model.C)
    )
    model.fleet_limit = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.C) <= model.num_vehicles
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.u[i]
            - mdl.u[j]
            + mdl.num_collection_points * mdl.x[i, j]
            <= mdl.num_collection_points - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.C,
        model.C,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance_matrix[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    # Each depot-rooted cycle represents one utilized truck. Unused trucks
    # remain at the depot and require no selected travel arcs.
    solver_failure = None
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failure = "solver_failed"

    # Success depends exclusively on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": solver_failure or "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}
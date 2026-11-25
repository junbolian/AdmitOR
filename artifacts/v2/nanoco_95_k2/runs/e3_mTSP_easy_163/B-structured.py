# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"C":[1,2,3,4,5,6,7,8],"A":"{(i,j) in N*N: i!=j}","P":"{(i,j) in C*C: i!=j}"},"params":{"coordinates":"(params['hosp_x'],params['hosp_y']) for node 0; (params[f'n{i}_x'],params[f'n{i}_y']) for i in C; descriptive only","distance":"params[f'dist_{min(i,j)}_{max(i,j)}'] for (i,j) in A; symmetric, nonnegative","fleet_count":"params['num_vehicles']; nonnegative integer"},"variables":{"x[i,j]":"binary for (i,j) in A; selected directed arc","u[i]":"real in [1,8] for i in C"},"constraints":["sum(x[i,j] for j in N if j!=i)=1 for i in C","sum(x[j,i] for j in N if j!=i)=1 for i in C","sum(x[0,j] for j in C)=fleet_count","sum(x[i,0] for i in C)=fleet_count","u[i]-u[j]+8*x[i,j]<=7 for (i,j) in P"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A)","route_interpretation":"Each depot-to-depot cycle is one nonempty route for an identical van."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(9))
    clinics = tuple(range(1, 9))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )
    clinic_pairs = tuple(
        (origin, destination)
        for origin in clinics
        for destination in clinics
        if origin != destination
    )
    clinic_count = len(clinics)

    coordinates = {
        0: (params["hosp_x"], params["hosp_y"]),
        **{
            clinic: (
                params[f"n{clinic}_x"],
                params[f"n{clinic}_y"],
            )
            for clinic in clinics
        },
    }
    distances = {
        (origin, destination): params[
            f"dist_{min(origin, destination)}_{max(origin, destination)}"
        ]
        for origin, destination in arcs
    }
    fleet_count = params["num_vehicles"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.clinics = pyo.Set(initialize=clinics, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.clinic_pairs = pyo.Set(dimen=2, initialize=clinic_pairs)

    # Coordinates are retained as descriptive data. Supplied travel
    # distances, rather than coordinate-derived distances, determine cost.
    model.coordinate_x = pyo.Param(
        model.nodes,
        initialize={node: coordinates[node][0] for node in nodes},
        within=pyo.Reals,
    )
    model.coordinate_y = pyo.Param(
        model.nodes,
        initialize={node: coordinates[node][1] for node in nodes},
        within=pyo.Reals,
    )
    model.distance = pyo.Param(
        model.arcs,
        initialize=distances,
        within=pyo.NonNegativeReals,
    )
    model.fleet_count = pyo.Param(
        initialize=fleet_count,
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.clinics,
        domain=pyo.Reals,
        bounds=(1, clinic_count),
    )

    def clinic_departure_rule(instance, clinic):
        return sum(
            instance.x[clinic, destination]
            for destination in instance.nodes
            if destination != clinic
        ) == 1

    model.clinic_departures = pyo.Constraint(
        model.clinics,
        rule=clinic_departure_rule,
    )

    def clinic_arrival_rule(instance, clinic):
        return sum(
            instance.x[origin, clinic]
            for origin in instance.nodes
            if origin != clinic
        ) == 1

    model.clinic_arrivals = pyo.Constraint(
        model.clinics,
        rule=clinic_arrival_rule,
    )

    model.depot_departures = pyo.Constraint(
        expr=sum(
            model.x[0, clinic] for clinic in model.clinics
        ) == model.fleet_count
    )
    model.depot_arrivals = pyo.Constraint(
        expr=sum(
            model.x[clinic, 0] for clinic in model.clinics
        ) == model.fleet_count
    )

    def subtour_elimination_rule(instance, origin, destination):
        return (
            instance.u[origin]
            - instance.u[destination]
            + clinic_count * instance.x[origin, destination]
            <= clinic_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.clinic_pairs,
        rule=subtour_elimination_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
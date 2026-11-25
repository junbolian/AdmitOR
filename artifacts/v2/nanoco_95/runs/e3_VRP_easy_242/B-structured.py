# IR: {"sets":{"N":"{0,...,num_clinics}","C":"N\\{0}","A":"{(i,j) in N*N:i!=j}","D":"{0,1}"},"params":{"coordinates":"node coordinates indexed by N*D; metadata only","distance_matrix":"route distances indexed by N*N","num_vehicles":"required number of nonempty depot routes","num_clinics":"number of clinics"},"variables":{"x[i,j]":"Binary for (i,j) in A; selected directed arc","u[i]":"Real in [1,num_clinics] for i in C; clinic ordering"},"constraints":{"clinic_in":"sum(x[i,j] for i in N if i!=j)=1 for j in C","clinic_out":"sum(x[i,j] for j in N if j!=i)=1 for i in C","depot_out":"sum(x[0,j] for j in C)=num_vehicles","depot_in":"sum(x[i,0] for i in C)=num_vehicles","subtour":"u[i]-u[j]+num_clinics*x[i,j]<=num_clinics-1 for distinct i,j in C"},"objective":"minimize sum(distance_matrix[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coordinates = params["coordinates"]
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]
    num_clinics = params["num_clinics"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(
        initialize=range(num_clinics + 1), ordered=True
    )
    model.clinics = pyo.Set(
        initialize=range(1, num_clinics + 1), ordered=True
    )
    model.dimensions = pyo.Set(initialize=range(2), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(num_clinics + 1)
            for destination in range(num_clinics + 1)
            if origin != destination
        ],
    )

    model.clinic_count = pyo.Param(
        initialize=num_clinics, within=pyo.PositiveIntegers
    )
    model.vehicle_count = pyo.Param(
        initialize=num_vehicles, within=pyo.PositiveIntegers
    )
    model.node_coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize=lambda mdl, node, dimension: coordinates[node][dimension],
        within=pyo.Reals,
    )
    model.route_distance = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda mdl, origin, destination: (
            distance_matrix[origin][destination]
        ),
        within=pyo.NonNegativeReals,
    )

    model.arc_used = pyo.Var(model.arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.clinics,
        domain=pyo.Reals,
        bounds=(1, num_clinics),
    )

    def clinic_in_rule(mdl, clinic):
        return sum(
            mdl.arc_used[origin, clinic]
            for origin in mdl.nodes
            if origin != clinic
        ) == 1

    model.clinic_in = pyo.Constraint(
        model.clinics, rule=clinic_in_rule
    )

    def clinic_out_rule(mdl, clinic):
        return sum(
            mdl.arc_used[clinic, destination]
            for destination in mdl.nodes
            if destination != clinic
        ) == 1

    model.clinic_out = pyo.Constraint(
        model.clinics, rule=clinic_out_rule
    )

    model.depot_out = pyo.Constraint(
        expr=sum(
            model.arc_used[0, clinic] for clinic in model.clinics
        ) == model.vehicle_count
    )
    model.depot_in = pyo.Constraint(
        expr=sum(
            model.arc_used[clinic, 0] for clinic in model.clinics
        ) == model.vehicle_count
    )

    def subtour_rule(mdl, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            mdl.visit_order[origin]
            - mdl.visit_order[destination]
            + mdl.clinic_count * mdl.arc_used[origin, destination]
            <= mdl.clinic_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.clinics,
        model.clinics,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.route_distance[origin, destination]
            * model.arc_used[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    # Each depot cycle represents one identical van's nonempty route.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
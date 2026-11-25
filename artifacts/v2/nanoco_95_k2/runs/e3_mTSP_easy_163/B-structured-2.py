# IR: {"sets":{"N":"{0,...,8}","C":"{1,...,8}","A":"{(i,j) in N x N: i != j}","P":"{(i,j) in C x C: i != j}"},"params":{"coord_x[0]":"params['hosp_x']","coord_y[0]":"params['hosp_y']","coord_x[i in C]":"params[f'n{i}_x']","coord_y[i in C]":"params[f'n{i}_y']","distance[i,j in A]":"params[f'dist_{min(i,j)}_{max(i,j)}']","fleet_size":"params['num_vehicles']","coordinates_role":"node metadata; supplied distances define travel costs"},"variables":{"arc_used[i,j in A]":"binary","visit_order[i in C]":"continuous in [1,|C|]"},"constraints":["For each i in C: sum(j in N, j != i) arc_used[i,j] = 1.","For each j in C: sum(i in N, i != j) arc_used[i,j] = 1.","sum(j in C) arc_used[0,j] = fleet_size.","sum(i in C) arc_used[i,0] = fleet_size.","For each (i,j) in P: visit_order[i] - visit_order[j] + |C|*arc_used[i,j] <= |C|-1."],"objective":"Minimize sum((i,j) in A) distance[i,j]*arc_used[i,j]."}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = tuple(range(9))
    clinics = tuple(range(1, 9))
    arcs = tuple((i, j) for i in nodes for j in nodes if i != j)
    clinic_pairs = tuple((i, j) for i in clinics for j in clinics if i != j)
    clinic_count = len(clinics)

    x_coordinates = {0: params["hosp_x"]}
    y_coordinates = {0: params["hosp_y"]}
    for i in clinics:
        x_coordinates[i] = params[f"n{i}_x"]
        y_coordinates[i] = params[f"n{i}_y"]

    distances = {
        (i, j): params[f"dist_{min(i, j)}_{max(i, j)}"]
        for i, j in arcs
    }

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.clinics = pyo.Set(initialize=clinics, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.clinic_pairs = pyo.Set(
        dimen=2, initialize=clinic_pairs, ordered=True
    )

    model.coord_x = pyo.Param(
        model.nodes, initialize=x_coordinates, within=pyo.Reals
    )
    model.coord_y = pyo.Param(
        model.nodes, initialize=y_coordinates, within=pyo.Reals
    )
    model.distance = pyo.Param(
        model.arcs, initialize=distances, within=pyo.NonNegativeReals
    )
    model.fleet_size = pyo.Param(
        initialize=params["num_vehicles"],
        within=pyo.NonNegativeIntegers,
    )

    model.arc_used = pyo.Var(model.arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.clinics,
        domain=pyo.Reals,
        bounds=(1, clinic_count),
    )

    def clinic_departure_rule(instance, i):
        return sum(
            instance.arc_used[i, j]
            for j in instance.nodes
            if j != i
        ) == 1

    def clinic_arrival_rule(instance, j):
        return sum(
            instance.arc_used[i, j]
            for i in instance.nodes
            if i != j
        ) == 1

    model.clinic_departures = pyo.Constraint(
        model.clinics, rule=clinic_departure_rule
    )
    model.clinic_arrivals = pyo.Constraint(
        model.clinics, rule=clinic_arrival_rule
    )

    # Each depot departure starts a nonempty route, so every van is used.
    model.depot_departures = pyo.Constraint(
        expr=sum(model.arc_used[0, j] for j in model.clinics)
        == model.fleet_size
    )
    model.depot_arrivals = pyo.Constraint(
        expr=sum(model.arc_used[i, 0] for i in model.clinics)
        == model.fleet_size
    )

    # Eliminate cycles consisting solely of clinics.
    def subtour_rule(instance, i, j):
        return (
            instance.visit_order[i]
            - instance.visit_order[j]
            + clinic_count * instance.arc_used[i, j]
            <= clinic_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.clinic_pairs, rule=subtour_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.arc_used[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
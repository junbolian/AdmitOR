# IR: {"sets":{"C":"{0,...,num_cities-1}","A":"{(i,j) in C x C: i!=j}","F":"{(i,j) in A: j!=0}"},"params":{"num_cities":"params['num_cities']; frozen at 7","distance[i,j]":"params['distance_i_j'] for (i,j) in A","L":"params['position_lower_bound']","U":"params['position_upper_bound']","M":"U-L+1"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer in [L,U] for i in C"},"constraints":["sum(j:(i,j) in A) x[i,j]=1 for i in C","sum(i:(i,j) in A) x[i,j]=1 for j in C","u[0]=L","u[j]>=u[i]+1-M*(1-x[i,j]) for (i,j) in F"],"objective":"minimize sum((i,j) in A) distance[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    if num_cities != 7:
        raise ValueError("num_cities must equal the frozen index-set size of 7.")

    lower_bound = params["position_lower_bound"]
    upper_bound = params["position_upper_bound"]

    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, int(num_cities) - 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )
    model.forward_arcs = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i, j in model.arcs if j != 0],
    )

    model.city_count = pyo.Param(initialize=num_cities)
    model.position_lb = pyo.Param(initialize=lower_bound)
    model.position_ub = pyo.Param(initialize=upper_bound)
    model.order_big_m = pyo.Param(
        initialize=upper_bound - lower_bound + 1
    )
    model.travel_distance = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"distance_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.route_selected = pyo.Var(model.arcs, domain=pyo.Binary)
    model.tour_position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=(lower_bound, upper_bound),
    )

    def departure_rule(instance, i):
        return sum(
            instance.route_selected[i, j]
            for j in instance.cities
            if j != i
        ) == 1

    model.one_departure = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, j):
        return sum(
            instance.route_selected[i, j]
            for i in instance.cities
            if i != j
        ) == 1

    model.one_arrival = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.start_position = pyo.Constraint(
        expr=model.tour_position[0] == model.position_lb
    )

    def sequence_rule(instance, i, j):
        return (
            instance.tour_position[j]
            >= instance.tour_position[i]
            + 1
            - instance.order_big_m
            * (1 - instance.route_selected[i, j])
        )

    # Excluding arcs returning to City 0 permits the complete tour to close.
    # Strict position increases eliminate every cycle excluding City 0.
    # Together with the degree constraints, this forces one complete tour
    # and distinct positions for all cities.
    model.visit_sequence = pyo.Constraint(
        model.forward_arcs, rule=sequence_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.route_selected[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
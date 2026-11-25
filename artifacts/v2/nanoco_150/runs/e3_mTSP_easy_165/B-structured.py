# IR: {"sets":{"N":"{0,...,9}","C":"N minus {0}","A":"{(i,j) in N x N: i != j}","XY":"{'x','y'}"},"params":{"K":"params['num_vehicles']; nonnegative integer","coord[n,a]":"params['node{n}_{a}']; frozen, unused","d[i,j]":"params['dist_{min(i,j)}_{max(i,j)}']; symmetric road distance","q":"|C|; structural constant"},"variables":{"x[i,j]":"binary; selected directed arc","u[i]":"continuous in [1,q]; customer ordering"},"constraints":["For each i in C: sum_{j in N, j != i} x[i,j] = 1.","For each j in C: sum_{i in N, i != j} x[i,j] = 1.","sum_{j in C} x[0,j] = K.","sum_{i in C} x[i,0] = K.","For distinct i,j in C: u[i] - u[j] + q*x[i,j] <= q-1."],"objective":"Minimize sum_{(i,j) in A} d[i,j]*x[i,j].","interpretation":"Exactly K nonempty depot-to-depot routes; identical vehicles need no explicit labels."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(10), ordered=True)
    model.customers = pyo.Set(initialize=range(1, 10), ordered=True)
    model.axes = pyo.Set(initialize=("x", "y"), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ),
        ordered=True,
    )

    model.vehicle_count = pyo.Param(
        initialize=params["num_vehicles"],
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )
    model.coordinates = pyo.Param(
        model.nodes,
        model.axes,
        initialize={
            (i, axis): params[f"node{i}_{axis}"]
            for i in model.nodes
            for axis in model.axes
        },
        within=pyo.Reals,
        mutable=False,
    )
    model.distance = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"dist_{min(i, j)}_{max(i, j)}"]
            for i, j in model.arcs
        },
        within=pyo.NonNegativeReals,
        mutable=False,
    )

    customer_count = len(model.customers)

    model.route_arc = pyo.Var(model.arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.customers,
        domain=pyo.Reals,
        bounds=(1, customer_count),
    )

    def customer_departure_rule(instance, i):
        return sum(
            instance.route_arc[i, j]
            for j in instance.nodes
            if j != i
        ) == 1

    model.customer_departure = pyo.Constraint(
        model.customers,
        rule=customer_departure_rule,
    )

    def customer_arrival_rule(instance, j):
        return sum(
            instance.route_arc[i, j]
            for i in instance.nodes
            if i != j
        ) == 1

    model.customer_arrival = pyo.Constraint(
        model.customers,
        rule=customer_arrival_rule,
    )

    model.depot_departure = pyo.Constraint(
        expr=sum(
            model.route_arc[0, j] for j in model.customers
        ) == model.vehicle_count
    )
    model.depot_arrival = pyo.Constraint(
        expr=sum(
            model.route_arc[i, 0] for i in model.customers
        ) == model.vehicle_count
    )

    def subtour_elimination_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.visit_order[i]
            - instance.visit_order[j]
            + customer_count * instance.route_arc[i, j]
            <= customer_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.customers,
        model.customers,
        rule=subtour_elimination_rule,
    )

    model.total_mileage = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.route_arc[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Still determine success solely through objective retrieval below.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_mileage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
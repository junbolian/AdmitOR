# IR: {"sets":{"V":"{0,...,8}","C":"{1,...,8}","A":"{(i,j) in V x V: i != j}","D":"{0,1}"},"params":{"distance_matrix":"distance[i,j] on V x V","hub_coordinates":"coordinate[0,d] on D; geographic metadata","customer_coordinates":"coordinate[i,d] on C x D; geographic metadata","num_vehicles":"K, nonnegative integer"},"variables":{"x[i,j]":"binary on A","u[i]":"continuous in [1,|C|] on C","idle":"integer in [0,K]"},"constraints":["For each customer j: sum_i x[i,j] = 1.","For each customer i: sum_j x[i,j] = 1.","sum_j_in_C x[0,j] + idle = K.","sum_i_in_C x[i,0] + idle = K.","For distinct customers i,j: u[i] - u[j] + |C|*x[i,j] <= |C|-1."],"objective":"Minimize sum_(i,j)_in_A distance[i,j]*x[i,j]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    hub_coordinates = params["hub_coordinates"]
    customer_coordinates = params["customer_coordinates"]
    num_vehicles = params["num_vehicles"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(9), ordered=True)
    model.customers = pyo.Set(initialize=range(1, 9), ordered=True)
    model.dimensions = pyo.Set(initialize=range(2), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
    )

    model.distance = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda _, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )
    model.fleet_size = pyo.Param(
        initialize=num_vehicles,
        within=pyo.NonNegativeIntegers,
    )

    # Coordinates are metadata; the supplied road distances define travel costs.
    model.coordinate = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize=lambda _, i, d: (
            hub_coordinates[d]
            if i == 0
            else customer_coordinates[i - 1][d]
        ),
        within=pyo.Reals,
    )

    customer_count = len(model.customers)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.customers,
        domain=pyo.Reals,
        bounds=(1, customer_count),
    )
    model.idle = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, model.fleet_size),
    )

    def customer_incoming_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.nodes if i != j
        ) == 1

    model.customer_incoming = pyo.Constraint(
        model.customers,
        rule=customer_incoming_rule,
    )

    def customer_outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.nodes if j != i
        ) == 1

    model.customer_outgoing = pyo.Constraint(
        model.customers,
        rule=customer_outgoing_rule,
    )

    # Each nonidle vehicle corresponds to one depot-to-depot circuit.
    # Each idle vehicle represents the permitted zero-distance 0-to-0 route.
    model.depot_departures = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.customers)
        + model.idle
        == model.fleet_size
    )
    model.depot_returns = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in model.customers)
        + model.idle
        == model.fleet_size
    )

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[i]
            - instance.u[j]
            + customer_count * instance.x[i, j]
            <= customer_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.customers,
        model.customers,
        rule=subtour_rule,
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
        # APPsi raises this when its default solution loading finds no
        # feasible solution. Unrelated runtime errors must propagate.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
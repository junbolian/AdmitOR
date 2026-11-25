# IR: {"sets":{"N":"{0,...,8}","C":"{1,...,8}","K":"{0,...,num_vehicles-1}","A":"{(i,j) in N x N : i != j}"},"params":{"distance_matrix":"9x9 travel distances","num_vehicles":"number of available vans"},"variables":{"x[k,i,j]":"binary; van k traverses arc (i,j)","used[k]":"binary; van k has a nonempty route","u[k,i]":"continuous in [1,8]; customer ordering"},"constraints":["For each i in C: sum(k in K,j in N\\{i}) x[k,i,j] = 1.","For each k in K,i in C: sum(j in N\\{i}) x[k,i,j] = sum(j in N\\{i}) x[k,j,i].","For each k in K: sum(j in C) x[k,0,j] = used[k].","For each k in K: sum(i in C) x[k,i,0] = used[k].","For each k in K,(i,j) in C x C with i != j: u[k,i]-u[k,j]+8*x[k,i,j] <= 7."],"objective":"minimize sum(k in K,(i,j) in A) distance_matrix[i][j]*x[k,i,j]","idle":"used[k]=0 represents an idle van at the depot, with zero travel cost"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 8)
    model.customers = pyo.RangeSet(1, 8)
    model.vehicles = pyo.Set(
        initialize=range(num_vehicles),
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(9)
            for destination in range(9)
            if origin != destination
        ],
    )

    model.travel_distance = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): distance_matrix[origin][destination]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.vehicles,
        model.arcs,
        domain=pyo.Binary,
    )
    model.used = pyo.Var(model.vehicles, domain=pyo.Binary)
    model.u = pyo.Var(
        model.vehicles,
        model.customers,
        domain=pyo.Reals,
        bounds=(1, 8),
    )

    def unique_service_rule(instance, customer):
        # Explicit tuples also handle an empty fleet as an infeasible constraint.
        outgoing = sum(
            instance.x[vehicle, customer, destination]
            for vehicle in instance.vehicles
            for destination in instance.nodes
            if destination != customer
        )
        return (1, outgoing, 1)

    model.unique_service = pyo.Constraint(
        model.customers,
        rule=unique_service_rule,
    )

    def customer_flow_rule(instance, vehicle, customer):
        return sum(
            instance.x[vehicle, customer, destination]
            for destination in instance.nodes
            if destination != customer
        ) == sum(
            instance.x[vehicle, origin, customer]
            for origin in instance.nodes
            if origin != customer
        )

    model.customer_flow = pyo.Constraint(
        model.vehicles,
        model.customers,
        rule=customer_flow_rule,
    )

    def depot_departure_rule(instance, vehicle):
        return sum(
            instance.x[vehicle, 0, customer]
            for customer in instance.customers
        ) == instance.used[vehicle]

    model.depot_departure = pyo.Constraint(
        model.vehicles,
        rule=depot_departure_rule,
    )

    def depot_return_rule(instance, vehicle):
        return sum(
            instance.x[vehicle, customer, 0]
            for customer in instance.customers
        ) == instance.used[vehicle]

    model.depot_return = pyo.Constraint(
        model.vehicles,
        rule=depot_return_rule,
    )

    def subtour_elimination_rule(instance, vehicle, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            instance.u[vehicle, origin]
            - instance.u[vehicle, destination]
            + 8 * instance.x[vehicle, origin, destination]
            <= 7
        )

    model.subtour_elimination = pyo.Constraint(
        model.vehicles,
        model.customers,
        model.customers,
        rule=subtour_elimination_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[origin, destination]
            * model.x[vehicle, origin, destination]
            for vehicle in model.vehicles
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
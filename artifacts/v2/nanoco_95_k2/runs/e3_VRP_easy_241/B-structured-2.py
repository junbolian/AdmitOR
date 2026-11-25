# IR: {"sets":{"N":"0..8","C":"1..8","K":"range(params['num_vehicles'])","A":"{(i,j) in N x N: i != j} union {(0,0)}"},"params":{"distance_matrix":"params['distance_matrix']","num_vehicles":"params['num_vehicles']"},"variables":{"x[k,i,j]":"binary, k in K, (i,j) in A; x[k,0,0]=1 denotes an idle vehicle","u[i]":"continuous in [1,8], i in C"},"constraints":["Unique service: sum(k in K, i in N where i != j) x[k,i,j] = 1 for each j in C.","Customer flow: sum(i in N where i != j) x[k,i,j] = sum(i in N where i != j) x[k,j,i] for each k in K, j in C.","Depot departure: sum(j in N) x[k,0,j] = 1 for each k in K.","Depot return: sum(i in N) x[k,i,0] = 1 for each k in K.","Subtour elimination: u[i]-u[j]+8*sum(k in K) x[k,i,j] <= 7 for each distinct i,j in C."],"objective":"Minimize sum(k in K, (i,j) in A) distance_matrix[i][j]*x[k,i,j]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 8)
    model.customers = pyo.RangeSet(1, 8)
    model.vehicles = pyo.Set(initialize=range(num_vehicles), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(9)
            for destination in range(9)
            if origin != destination or origin == 0
        ],
        ordered=True,
    )

    model.distance = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda mdl, origin, destination: distance_matrix[origin][destination],
    )

    model.x = pyo.Var(model.vehicles, model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.customers, domain=pyo.Reals, bounds=(1, 8))

    def unique_service_rule(mdl, customer):
        return (
            pyo.quicksum(
                mdl.x[vehicle, origin, customer]
                for vehicle in mdl.vehicles
                for origin in mdl.nodes
                if origin != customer
            )
            == 1
        )

    model.unique_service = pyo.Constraint(
        model.customers, rule=unique_service_rule
    )

    def customer_flow_rule(mdl, vehicle, customer):
        return pyo.quicksum(
            mdl.x[vehicle, origin, customer]
            for origin in mdl.nodes
            if origin != customer
        ) == pyo.quicksum(
            mdl.x[vehicle, customer, destination]
            for destination in mdl.nodes
            if destination != customer
        )

    model.customer_flow = pyo.Constraint(
        model.vehicles, model.customers, rule=customer_flow_rule
    )

    def depot_departure_rule(mdl, vehicle):
        return (
            pyo.quicksum(
                mdl.x[vehicle, 0, destination]
                for destination in mdl.nodes
            )
            == 1
        )

    model.depot_departure = pyo.Constraint(
        model.vehicles, rule=depot_departure_rule
    )

    def depot_return_rule(mdl, vehicle):
        return (
            pyo.quicksum(
                mdl.x[vehicle, origin, 0]
                for origin in mdl.nodes
            )
            == 1
        )

    model.depot_return = pyo.Constraint(
        model.vehicles, rule=depot_return_rule
    )

    def subtour_elimination_rule(mdl, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            mdl.u[origin]
            - mdl.u[destination]
            + 8
            * pyo.quicksum(
                mdl.x[vehicle, origin, destination]
                for vehicle in mdl.vehicles
            )
            <= 7
        )

    model.subtour_elimination = pyo.Constraint(
        model.customers,
        model.customers,
        rule=subtour_elimination_rule,
    )

    model.total_distance = pyo.Objective(
        expr=pyo.quicksum(
            model.distance[origin, destination]
            * model.x[vehicle, origin, destination]
            for vehicle in model.vehicles
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
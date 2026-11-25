# IR: {
#   "sets": {"N": "range(num_nodes)", "C": "range(1,num_customers+1)", "K": "range(num_vehicles)", "A": "[(i,j) for i in N for j in N if i!=j]", "D": ["x","y"]},
#   "params": {"num_nodes": "params['num_nodes']", "num_customers": "params['num_customers']", "num_vehicles": "params['num_vehicles']", "distance[i,j]": "params[f'distance_{i}_{j}'] for i,j in N", "coord[i,d]": "params[f'coord_{i}_{d}'] for i in N,d in D; descriptive metadata"},
#   "validation": ["num_nodes>=2", "num_customers=num_nodes-1", "num_vehicles>=1"],
#   "variables": {"route[i,j,k]": "binary for (i,j) in A,k in K", "visit_order[i,k]": "continuous in [1,num_customers] for i in C,k in K"},
#   "constraints": [
#     "customer_service[i]: sum(route[i,j,k] for j in N if j!=i for k in K)=1 for i in C",
#     "customer_flow[i,k]: sum(route[i,j,k] for j in N if j!=i)=sum(route[j,i,k] for j in N if j!=i) for i in C,k in K",
#     "depot_departure[k]: sum(route[0,j,k] for j in C)=1 for k in K",
#     "depot_return[k]: sum(route[i,0,k] for i in C)=1 for k in K",
#     "subtour_elimination[i,j,k]: visit_order[i,k]-visit_order[j,k]+num_customers*route[i,j,k]<=num_customers-1 for i,j in C with i!=j,k in K"
#   ],
#   "objective": "minimize total_mileage=sum(distance[i,j]*route[i,j,k] for (i,j) in A for k in K)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_customers = params["num_customers"]
    num_vehicles = params["num_vehicles"]

    if (
        num_nodes < 2
        or num_customers != num_nodes - 1
        or num_vehicles < 1
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    nodes = range(num_nodes)
    customers = range(1, num_customers + 1)
    vehicles = range(num_vehicles)

    distances = {
        (i, j): params[f"distance_{i}_{j}"]
        for i in nodes
        for j in nodes
    }
    coordinates = {
        (i, axis): params[f"coord_{i}_{axis}"]
        for i in nodes
        for axis in ("x", "y")
    }

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.C = pyo.Set(initialize=customers, ordered=True)
    model.K = pyo.Set(initialize=vehicles, ordered=True)
    model.D = pyo.Set(initialize=("x", "y"), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in nodes for j in nodes if i != j],
        ordered=True,
    )

    model.node_count = pyo.Param(initialize=num_nodes)
    model.customer_count = pyo.Param(initialize=num_customers)
    model.vehicle_count = pyo.Param(initialize=num_vehicles)
    model.distance = pyo.Param(
        model.N, model.N, initialize=distances, within=pyo.Reals
    )
    model.coord = pyo.Param(
        model.N, model.D, initialize=coordinates, within=pyo.Reals
    )

    model.route = pyo.Var(model.A, model.K, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.C,
        model.K,
        domain=pyo.Reals,
        bounds=(1, num_customers),
    )

    def customer_service_rule(instance, i):
        return pyo.quicksum(
            instance.route[i, j, k]
            for j in instance.N
            if j != i
            for k in instance.K
        ) == 1

    model.customer_service = pyo.Constraint(
        model.C, rule=customer_service_rule
    )

    def customer_flow_rule(instance, i, k):
        return pyo.quicksum(
            instance.route[i, j, k]
            for j in instance.N
            if j != i
        ) == pyo.quicksum(
            instance.route[j, i, k]
            for j in instance.N
            if j != i
        )

    model.customer_flow = pyo.Constraint(
        model.C, model.K, rule=customer_flow_rule
    )

    def depot_departure_rule(instance, k):
        return pyo.quicksum(
            instance.route[0, j, k] for j in instance.C
        ) == 1

    model.depot_departure = pyo.Constraint(
        model.K, rule=depot_departure_rule
    )

    def depot_return_rule(instance, k):
        return pyo.quicksum(
            instance.route[i, 0, k] for i in instance.C
        ) == 1

    model.depot_return = pyo.Constraint(
        model.K, rule=depot_return_rule
    )

    def subtour_elimination_rule(instance, i, j, k):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.visit_order[i, k]
            - instance.visit_order[j, k]
            + instance.customer_count * instance.route[i, j, k]
            <= instance.customer_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.C,
        model.C,
        model.K,
        rule=subtour_elimination_rule,
    )

    model.total_mileage = pyo.Objective(
        expr=pyo.quicksum(
            model.distance[i, j] * model.route[i, j, k]
            for i, j in model.A
            for k in model.K
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_mileage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
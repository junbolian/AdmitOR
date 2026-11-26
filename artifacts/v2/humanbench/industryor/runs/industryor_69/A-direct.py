import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["vehicle_capacity"]
    demand = params["customer_demand"]
    earliest = params["earliest_service_time"]
    latest = params["latest_service_time"]
    service = params["service_time"]
    xc = params["x_coordinate"]
    yc = params["y_coordinate"]

    n = len(demand)
    customers = list(range(1, n))
    nodes = list(range(n))

    # Euclidean distances
    dist = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                dx = xc[i] - xc[j]
                dy = yc[i] - yc[j]
                dist[(i, j)] = (dx * dx + dy * dy) ** 0.5

    # Upper bound on number of vehicles: tight from total demand
    total_demand = sum(demand[j] for j in customers)
    max_vehicles = min(n - 1, int(-(-total_demand // capacity)) + 5) if capacity > 0 else n - 1

    depot_latest = latest[0]

    # Big-M for time propagation
    horizon = depot_latest + max(service[j] for j in nodes) + max(
        dist[(0, j)] + dist[(j, 0)] for j in customers
    )
    if horizon <= 0:
        horizon = depot_latest + 1.0

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.customers = pyo.Set(initialize=customers, ordered=True)
    model.vehicles = pyo.Set(initialize=list(range(max_vehicles)), ordered=True)

    model.x = pyo.Var(
        [(i, j, k) for i in nodes for j in nodes if i != j for k in range(max_vehicles)],
        domain=pyo.Binary,
    )
    model.arrival = pyo.Var(
        [(i, k) for i in nodes for k in range(max_vehicles)],
        domain=pyo.NonNegativeReals,
    )
    model.start = pyo.Var(
        [(i, k) for i in nodes for k in range(max_vehicles)],
        domain=pyo.NonNegativeReals,
    )
    model.used = pyo.Var(range(max_vehicles), domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(
            dist[(i, j)] * mdl.x[i, j, k]
            for (i, j, k) in mdl.x
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once
    def assign_rule(mdl, j):
        return sum(mdl.x[i, j, k] for i in nodes for k in range(max_vehicles) if i != j) == 1

    model.assign_constraint = pyo.Constraint(model.customers, rule=assign_rule)

    # Flow conservation per vehicle per node
    def flow_rule(mdl, i, k):
        out_ = sum(mdl.x[i, j, k] for j in nodes if j != i)
        in_ = sum(mdl.x[j, i, k] for j in nodes if j != i)
        return out_ == in_

    model.flow_constraint = pyo.Constraint(model.nodes, model.vehicles, rule=flow_rule)

    # Depot departure <= 1 per vehicle and links to used
    def depot_depart_rule(mdl, k):
        return sum(mdl.x[0, j, k] for j in customers) <= mdl.used[k]

    model.depot_depart_constraint = pyo.Constraint(model.vehicles, rule=depot_depart_rule)

    # Vehicles used is non-increasing to break symmetry
    def vehicle_order_rule(mdl, k):
        if k == 0:
            return pyo.Constraint.Skip
        return mdl.used[k] <= mdl.used[k - 1]

    model.vehicle_order_constraint = pyo.Constraint(model.vehicles, rule=vehicle_order_rule)

    # Capacity
    def capacity_rule(mdl, k):
        return sum(demand[j] * mdl.x[i, j, k] for (i, j, k2) in mdl.x if k2 == k for j in [j]) <= capacity

    model.capacity_constraint = pyo.Constraint(model.vehicles, rule=capacity_rule)

    # Time window bounds on start
    def start_lb_rule(mdl, i, k):
        return mdl.start[i, k] >= earliest[i]

    model.start_lb_constraint = pyo.Constraint(model.nodes, model.vehicles, rule=start_lb_rule)

    def start_ub_rule(mdl, i, k):
        return mdl.start[i, k] <= latest[i]

    model.start_ub_constraint = pyo.Constraint(model.nodes, model.vehicles, rule=start_ub_rule)

    # Arrival <= start (wait if early)
    def arrival_start_rule(mdl, i, k):
        return mdl.arrival[i, k] <= mdl.start[i, k]

    model.arrival_start_constraint = pyo.Constraint(model.nodes, model.vehicles, rule=arrival_start_rule)

    # Depot start at 0
    def depot_start_rule(mdl, k):
        return mdl.start[0, k] == 0

    model.depot_start_constraint = pyo.Constraint(model.vehicles, rule=depot_start_rule)

    # Time propagation on arcs
    def time_link_rule(mdl, i, j, k):
        return mdl.arrival[j, k] >= (
            mdl.start[i, k] + service[i] + dist[(i, j)]
            - horizon * (1 - mdl.x[i, j, k])
        )

    model.time_link_constraint = pyo.Constraint(
        [(i, j, k) for (i, j, k) in model.x], rule=time_link_rule
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
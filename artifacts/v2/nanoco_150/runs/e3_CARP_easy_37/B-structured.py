# IR: {"sets":{"V":[0,1,2,3,4,5,6],"K":[0,1],"E_required":[[0,2],[0,5],[0,6],[3,4],[3,5]],"A":"all ordered pairs (i,j) in V with i!=j","S":"both orientations of every edge in E_required"},"params":{"vehicle_capacity":"params['vehicle_capacity']","service_demand_0_2":"params['service_demand_0_2']","service_demand_0_5":"params['service_demand_0_5']","service_demand_0_6":"params['service_demand_0_6']","service_demand_3_4":"params['service_demand_3_4']","service_demand_3_5":"params['service_demand_3_5']","distance_matrix":"params['distance_matrix']; nested 7x7 or flat row-major length 49"},"variables":{"x[k,i,j]":"nonnegative integer traversal count on A","y[k,i,j]":"binary service indicator on S","f[k,i,j]":"nonnegative continuous connectivity flow on A"},"definitions":{"b[k,v]":"sum of y[k,i,j] over service arcs incident to v","B":"2*|E_required|"},"constraints":["For each required edge {i,j}: sum_k(y[k,i,j]+y[k,j,i])=1.","For each vehicle k: sum_(i,j in S) demand[{i,j}]*y[k,i,j]<=vehicle_capacity.","For each vehicle k: sum_(i,j in S) y[k,i,j]>=1.","For each k,v: sum_(j!=v) x[k,v,j]=sum_(i!=v) x[k,i,v].","For each k,(i,j) in S: x[k,i,j]>=y[k,i,j].","For each k,v!=0: sum_(i!=v) f[k,i,v]-sum_(j!=v) f[k,v,j]=b[k,v].","For each k: sum_(j!=0) f[k,0,j]-sum_(i!=0) f[k,i,0]=sum_(v!=0) b[k,v].","For each k,(i,j) in A: f[k,i,j]<=B*x[k,i,j]."],"objective":"minimize sum_(k,(i,j) in A) distance_matrix[i,j]*x[k,i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(7))
    vehicles = tuple(range(2))
    required_edges = ((0, 2), (0, 5), (0, 6), (3, 4), (3, 5))
    travel_arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )
    service_arcs = tuple(
        oriented_arc
        for origin, destination in required_edges
        for oriented_arc in ((origin, destination), (destination, origin))
    )

    vehicle_capacity = params["vehicle_capacity"]
    edge_demands = {
        (0, 2): params["service_demand_0_2"],
        (0, 5): params["service_demand_0_5"],
        (0, 6): params["service_demand_0_6"],
        (3, 4): params["service_demand_3_4"],
        (3, 5): params["service_demand_3_5"],
    }
    distance_matrix = params["distance_matrix"]

    if len(distance_matrix) == 49:
        travel_costs = {
            (origin, destination): distance_matrix[7 * origin + destination]
            for origin, destination in travel_arcs
        }
    else:
        travel_costs = {
            (origin, destination): distance_matrix[origin][destination]
            for origin, destination in travel_arcs
        }

    oriented_demands = {}
    for origin, destination in required_edges:
        oriented_demands[origin, destination] = edge_demands[origin, destination]
        oriented_demands[destination, origin] = edge_demands[origin, destination]

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=nodes, ordered=True)
    model.K = pyo.Set(initialize=vehicles, ordered=True)
    model.E_required = pyo.Set(
        dimen=2, initialize=required_edges, ordered=True
    )
    model.A = pyo.Set(dimen=2, initialize=travel_arcs, ordered=True)
    model.S = pyo.Set(dimen=2, initialize=service_arcs, ordered=True)

    model.hopper_limit = pyo.Param(
        initialize=vehicle_capacity, within=pyo.NonNegativeReals
    )
    model.travel_cost = pyo.Param(
        model.A, initialize=travel_costs, within=pyo.NonNegativeReals
    )
    model.service_load = pyo.Param(
        model.S, initialize=oriented_demands, within=pyo.NonNegativeReals
    )

    model.x = pyo.Var(model.K, model.A, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(model.K, model.S, domain=pyo.Binary)
    model.f = pyo.Var(model.K, model.A, domain=pyo.NonNegativeReals)

    def endpoint_load_rule(mdl, vehicle, node):
        return sum(
            mdl.y[vehicle, origin, destination]
            for origin, destination in mdl.S
            if origin == node or destination == node
        )

    model.endpoint_load = pyo.Expression(
        model.K, model.V, rule=endpoint_load_rule
    )

    def service_once_rule(mdl, origin, destination):
        return sum(
            mdl.y[vehicle, origin, destination]
            + mdl.y[vehicle, destination, origin]
            for vehicle in mdl.K
        ) == 1

    model.service_once = pyo.Constraint(
        model.E_required, rule=service_once_rule
    )

    def capacity_rule(mdl, vehicle):
        return sum(
            mdl.service_load[origin, destination]
            * mdl.y[vehicle, origin, destination]
            for origin, destination in mdl.S
        ) <= mdl.hopper_limit

    model.capacity_limit = pyo.Constraint(model.K, rule=capacity_rule)

    def nonempty_route_rule(mdl, vehicle):
        return sum(
            mdl.y[vehicle, origin, destination]
            for origin, destination in mdl.S
        ) >= 1

    model.nonempty_route = pyo.Constraint(model.K, rule=nonempty_route_rule)

    def traversal_balance_rule(mdl, vehicle, node):
        return sum(
            mdl.x[vehicle, node, other]
            for other in mdl.V
            if other != node
        ) == sum(
            mdl.x[vehicle, other, node]
            for other in mdl.V
            if other != node
        )

    model.traversal_balance = pyo.Constraint(
        model.K, model.V, rule=traversal_balance_rule
    )

    def service_traversal_rule(mdl, vehicle, origin, destination):
        return (
            mdl.x[vehicle, origin, destination]
            >= mdl.y[vehicle, origin, destination]
        )

    model.service_traversal = pyo.Constraint(
        model.K, model.S, rule=service_traversal_rule
    )

    def connectivity_balance_rule(mdl, vehicle, node):
        incoming = sum(
            mdl.f[vehicle, other, node]
            for other in mdl.V
            if other != node
        )
        outgoing = sum(
            mdl.f[vehicle, node, other]
            for other in mdl.V
            if other != node
        )
        if node == 0:
            return outgoing - incoming == sum(
                mdl.endpoint_load[vehicle, other]
                for other in mdl.V
                if other != 0
            )
        return incoming - outgoing == mdl.endpoint_load[vehicle, node]

    model.connectivity_balance = pyo.Constraint(
        model.K, model.V, rule=connectivity_balance_rule
    )

    # At most two endpoint-flow units are needed per required segment.
    flow_bound = 2 * len(required_edges)

    def connectivity_capacity_rule(mdl, vehicle, origin, destination):
        return (
            mdl.f[vehicle, origin, destination]
            <= flow_bound * mdl.x[vehicle, origin, destination]
        )

    model.connectivity_capacity = pyo.Constraint(
        model.K, model.A, rule=connectivity_capacity_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[vehicle, origin, destination]
            for vehicle in model.K
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    # APPsi raises this RuntimeError when no feasible solution can be loaded.
    # Leave variables uninitialized so objective retrieval determines success.
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    # exception=False avoids Pyomo logging an uninitialized-value error.
    # Explicitly raise so failure is still determined by objective retrieval.
    try:
        if pyo.value(model.total_distance, exception=False) is None:
            raise ValueError("Objective unavailable")
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
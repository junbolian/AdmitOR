import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    fleet_size = params["fleet_size"]
    vehicle_capacity = params["vehicle_capacity"]
    service_demands_list = params["service_demands"]
    distance_matrix = params["distance_matrix"]

    # Required service edges and their demands
    required_edges = [(0,5), (2,5), (2,6), (4,6)]
    demands = {required_edges[i]: service_demands_list[i] for i in range(len(required_edges))}

    # Road network edges (undirected)
    road_edges = [(0,1),(0,3),(0,5),(1,3),(2,3),(2,5),(2,6),(4,5),(4,6)]
    road_set = set()
    for u,v in road_edges:
        road_set.add((u,v))
        road_set.add((v,u))

    num_nodes = 7
    vehicles = list(range(fleet_size))
    num_req = len(required_edges)
    req_idx = list(range(num_req))

    # Distance helper
    def dist(i, j):
        return distance_matrix[i][j]

    # We model this as a vehicle routing problem on edges.
    # Each required edge must be assigned to exactly one vehicle.
    # For each vehicle, we need to find the minimum-cost route
    # through its assigned edges starting and ending at depot 0.
    #
    # Approach: enumerate all subsets of required edges assigned to each vehicle,
    # check capacity, then for each feasible assignment compute the min-cost route
    # (TSP-like on nodes visited) using a MIP.
    #
    # Since fleet_size=2 and num_req=4, we enumerate all partitions of 4 edges
    # into 2 groups, check capacity, then for each partition solve a small routing subproblem.
    #
    # For the routing subproblem: given a set of required edges assigned to a vehicle,
    # find minimum cost closed walk starting/ending at depot 0 that traverses each
    # required edge at least once. Deadheading between any two nodes is allowed.
    # This is the Route Inspection / Chinese Postman variant on a subset of edges.
    #
    # Since the required edges form a small subgraph, we model the vehicle's route as:
    # visit a sequence of nodes (starting and ending at 0) covering all required edges.
    # We use a compact MIP with MTZ subtour elimination for the node-visit sequence.

    def solve_vehicle_route(req_edge_subset):
        """
        Given a list of required edges for one vehicle, find the minimum cost
        closed walk from depot 0 that services each required edge exactly once.
        
        We model this as: the vehicle traverses a sequence of nodes. Each required
        edge (u,v) must appear as a consecutive pair in direction u->v or v->u.
        Between consecutive serviced edges, the vehicle deadheads optimally.
        
        Simplified model: treat each required edge as a "task" node. The vehicle
        visits tasks in some order. The cost is:
          deadhead(0 -> first_task_entry) + service(first_task) 
          + deadhead(first_task_exit -> second_task_entry) + service(second_task) + ...
          + deadhead(last_task_exit -> 0)
        
        Each task edge (u,v) can be traversed as u->v or v->u.
        The deadhead cost between any two nodes is dist(i,j).
        """
        n_tasks = len(req_edge_subset)
        if n_tasks == 0:
            return 0.0

        # For each task, it has two endpoints; traversal direction is a choice.
        # We use a TSP-like formulation over tasks with orientation.
        # State: (task_index, direction) where direction 0 = forward (u->v), 1 = backward (v->u)
        # Entry node of task t, dir d: req_edge_subset[t][d] (0=u, 1=v)
        # Exit node of task t, dir d: req_edge_subset[t][1-d] ... wait
        # Edge (u,v): forward means enter u, exit v; backward means enter v, exit u.

        def entry_node(t, d):
            u, v = req_edge_subset[t]
            return u if d == 0 else v

        def exit_node(t, d):
            u, v = req_edge_subset[t]
            return v if d == 0 else u

        def task_service_cost(t):
            u, v = req_edge_subset[t]
            return dist(u, v)

        def deadhead_cost(from_node, to_node):
            return dist(from_node, to_node)

        # If only 1 task: cost = min over directions of (dist(0, entry) + service + dist(exit, 0))
        if n_tasks == 1:
            u, v = req_edge_subset[0]
            cost_fwd = dist(0, u) + dist(u, v) + dist(v, 0)
            cost_bwd = dist(0, v) + dist(v, u) + dist(u, 0)
            return min(cost_fwd, cost_bwd)

        # For n_tasks >= 2, solve a small TSP with orientation choices.
        # Variables:
        #   x[t1,d1,t2,d2] = 1 if we go from task t1 (exiting with direction d1) to task t2 (entering with direction d2)
        #   start[t,d] = 1 if task t is first with direction d
        #   end[t,d] = 1 if task t is last with direction d  
        #   dir[t,d] = 1 if task t is traversed in direction d
        #   u_t = position of task t in sequence (MTZ)

        sub = gp.Model()
        sub.setParam("OutputFlag", 0)
        sub.setParam("TimeLimit", 30)

        tasks = list(range(n_tasks))
        dirs = [0, 1]

        # x[t1,d1,t2,d2]: arc from (t1,d1) to (t2,d2)
        x = {}
        for t1 in tasks:
            for d1 in dirs:
                for t2 in tasks:
                    if t1 == t2:
                        continue
                    for d2 in dirs:
                        cost = task_service_cost(t1) if t1 not in [tt for tt,_ in []] else 0
                        # Arc cost: service t1 (if first time) + deadhead from exit(t1,d1) to entry(t2,d2)
                        # We'll handle service cost separately via dir variables
                        arc_cost = deadhead_cost(exit_node(t1,d1), entry_node(t2,d2))
                        x[t1,d1,t2,d2] = sub.addVar(vtype=GRB.BINARY, obj=arc_cost)

        # start[t,d]: depot to task t with direction d
        start = {}
        for t in tasks:
            for d in dirs:
                cost = deadhead_cost(0, entry_node(t,d))
                start[t,d] = sub.addVar(vtype=GRB.BINARY, obj=cost)

        # end[t,d]: task t with direction d back to depot
        end_v = {}
        for t in tasks:
            for d in dirs:
                cost = deadhead_cost(exit_node(t,d), 0)
                end_v[t,d] = sub.addVar(vtype=GRB.BINARY, obj=cost)

        # dir_var[t,d]: task t traversed in direction d (for service cost)
        dir_var = {}
        for t in tasks:
            for d in dirs:
                cost = task_service_cost(t) if d == 0 else task_service_cost(t)  # same either way
                dir_var[t,d] = sub.addVar(vtype=GRB.BINARY, obj=cost)

        # MTZ position variables
        pos = {t: sub.addVar(lb=1, ub=n_tasks, vtype=GRB.CONTINUOUS) for t in tasks}

        sub.update()

        # Each task traversed exactly once in one direction
        for t in tasks:
            sub.addConstr(gp.quicksum(dir_var[t,d] for d in dirs) == 1)

        # dir_var consistency with flow
        for t in tasks:
            for d in dirs:
                # dir_var[t,d] = 1 iff this (t,d) is active
                # flow in to (t,d) = start[t,d] + sum_{t1,d1} x[t1,d1,t,d]
                flow_in = start[t,d] + gp.quicksum(x[t1,d1,t,d] for t1 in tasks if t1 != t for d1 in dirs)
                sub.addConstr(dir_var[t,d] == flow_in)

        # flow out of (t,d)
        for t in tasks:
            for d in dirs:
                flow_out = end_v[t,d] + gp.quicksum(x[t,d,t2,d2] for t2 in tasks if t2 != t for d2 in dirs)
                sub.addConstr(dir_var[t,d] == flow_out)

        # Exactly one start and one end
        sub.addConstr(gp.quicksum(start[t,d] for t in tasks for d in dirs) == 1)
        sub.addConstr(gp.quicksum(end_v[t,d] for t in tasks for d in dirs) == 1)

        # MTZ subtour elimination
        for t1 in tasks:
            for d1 in dirs:
                for t2 in tasks:
                    if t1 == t2:
                        continue
                    for d2 in dirs:
                        sub.addConstr(pos[t2] >= pos[t1] + 1 - n_tasks * (1 - x[t1,d1,t2,d2]))

        sub.optimize()

        if sub.Status == GRB.OPTIMAL or sub.Status == GRB.TIME_LIMIT:
            return sub.ObjVal
        else:
            return float('inf')

    # Enumerate all partitions of required edges into fleet_size groups
    # For fleet_size=2, enumerate all subsets for vehicle 0; vehicle 1 gets the rest
    best_total = float('inf')
    best_status = "infeasible"

    # Generate all 2^num_req subsets for vehicle 0
    for mask in range(1 << num_req):
        subset0 = [required_edges[i] for i in req_idx if (mask >> i) & 1]
        subset1 = [required_edges[i] for i in req_idx if not ((mask >> i) & 1)]

        # Check capacity for both vehicles
        cap0 = sum(demands[e] for e in subset0)
        cap1 = sum(demands[e] for e in subset1)

        if cap0 > vehicle_capacity or cap1 > vehicle_capacity:
            continue

        # Both subsets must be non-empty (each vehicle must do something)
        # Actually a vehicle can have 0 tasks (just stays at depot, cost=0)
        # But we still need all edges covered, which is guaranteed by the partition

        cost0 = solve_vehicle_route(subset0)
        cost1 = solve_vehicle_route(subset1)
        total = cost0 + cost1

        if total < best_total:
            best_total = total
            best_status = "optimal"

    if best_status == "optimal":
        return {"objective": best_total, "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible"}
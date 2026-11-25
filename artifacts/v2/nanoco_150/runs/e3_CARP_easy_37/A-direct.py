def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    # ---------------------------------------------------------------
    # Data
    # ---------------------------------------------------------------
    capacity = params["vehicle_capacity"]
    dist_flat = params["distance_matrix"]
    D = [[dist_flat[i * 7 + j] for j in range(7)] for i in range(7)]

    # Mandatory segments: (edge id, node u, node v, demand)
    mandatory = [
        ("e01", 0, 2, params["service_demand_0_2"]),
        ("e02", 0, 5, params["service_demand_0_5"]),
        ("e03", 0, 6, params["service_demand_0_6"]),
        ("e04", 3, 4, params["service_demand_3_4"]),
        ("e05", 3, 5, params["service_demand_3_5"]),
    ]
    edges = [e[0] for e in mandatory]
    demand = {e[0]: e[3] for e in mandatory}

    vehicles = [0, 1]
    nodes = list(range(7))
    depot = 0

    # Arc set: all ordered pairs of distinct nodes
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    # For each mandatory edge, allow traversal in either direction ->
    # the edge is "served" by whichever directed arc (u,v) or (v,u) is chosen.
    # We model service by a binary per (edge, direction, vehicle).

    model = pyo.ConcreteModel()

    # ---------------------------------------------------------------
    # Variables
    # ---------------------------------------------------------------
    model.x = pyo.Var(arcs, vehicles, domain=pyo.Binary)      # vehicle k traverses arc (i,j)
    model.y = pyo.Var(edges, vehicles, domain=pyo.Binary)     # vehicle k serves edge e
    model.z = pyo.Var(
        [(e, u, v, k) for (e, u, v, d) in mandatory for k in vehicles for (u, v) in [(u, v), (v, u)]],
        domain=pyo.Binary,
    )  # vehicle k serves edge e in direction u->v

    # ---------------------------------------------------------------
    # Objective: minimize total travel distance over all arcs used
    # ---------------------------------------------------------------
    model.obj = pyo.Objective(
        expr=sum(D[i][j] * model.x[(i, j), k] for (i, j) in arcs for k in vehicles),
        sense=pyo.minimize,
    )

    # ---------------------------------------------------------------
    # Constraints
    # ---------------------------------------------------------------
    # 1) Each mandatory edge served exactly once (overall)
    model.serve_once = pyo.Constraint(
        edges,
        rule=lambda m, e: sum(m.y[e, k] for k in vehicles) == 1,
    )

    # 2) Service direction linking: serving edge e in direction u->v
    #    implies y[e,k]=1 and x[(u,v),k]=1
    z_list = [(e, u, v, k) for (e, a, b, d) in mandatory for k in vehicles for (u, v) in [(a, b), (b, a)]]

    def z_server(m, e, u, v, k):
        return m.z[e, u, v, k] <= m.y[e, k]

    def z_arc(m, e, u, v, k):
        return m.z[e, u, v, k] <= m.x[(u, v), k]

    model.z_le_y = pyo.Constraint(z_list, rule=z_server)
    model.z_le_x = pyo.Constraint(z_list, rule=z_arc)

    # 3) If y[e,k]=1, at least one direction chosen for k
    def y_implies_z(m, e, k):
        dirs = []
        for (ee, a, b, d) in mandatory:
            if ee == e:
                dirs = [(a, b), (b, a)]
        return m.y[e, k] <= sum(m.z[e, u, v, k] for (u, v) in dirs)

    model.y_implies_z = pyo.Constraint([(e, k) for e in edges for k in vehicles], rule=y_implies_z)

    # 4) Capacity per vehicle
    model.capacity = pyo.Constraint(
        vehicles,
        rule=lambda m, k: sum(demand[e] * m.y[e, k] for e in edges) <= capacity,
    )

    # 5) Flow conservation at each non-depot node for each vehicle
    def flow_balance(m, k, n):
        out = sum(m.x[(n, j), k] for j in nodes if j != n)
        inn = sum(m.x[(i, n), k] for i in nodes if i != n)
        return out == inn

    model.flow = pyo.Constraint(
        [(k, n) for k in vehicles for n in nodes if n != depot], rule=flow_balance
    )

    # 6) Depot flow: each used vehicle departs exactly as often as it enters
    def depot_balance(m, k):
        out = sum(m.x[(depot, j), k] for j in nodes if j != depot)
        inn = sum(m.x[(i, depot), k] for i in nodes if i != depot)
        return out == inn

    model.depot_balance = pyo.Constraint(vehicles, rule=depot_balance)

    # 7) A vehicle that serves anything must leave the depot (used vehicle).
    #    Each vehicle can leave depot at most once (single route per vehicle).
    model.depot_out = pyo.Constraint(
        vehicles,
        rule=lambda m, k: sum(m.x[(depot, j), k] for j in nodes if j != depot) <= 1,
    )

    # 8) If a vehicle does not leave the depot, it can serve nothing.
    def used_link(m, k):
        used = sum(m.x[(depot, j), k] for j in nodes if j != depot)
        return sum(m.y[e, k] for e in edges) <= 5 * used

    model.used_link = pyo.Constraint(vehicles, rule=used_link)

    # ---------------------------------------------------------------
    # Solve
    # ---------------------------------------------------------------
    result = Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
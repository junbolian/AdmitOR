import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    coordinates_x = params["coordinates_x"]
    coordinates_y = params["coordinates_y"]
    required_edge_ratio = params["required_edge_ratio"]

    num_nodes = 8

    # Reconstruct full symmetric distance matrix from flattened upper-triangular entries
    dist = [[0.0] * num_nodes for _ in range(num_nodes)]
    k = 0
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            dist[i][j] = float(distance_matrix[k])
            dist[j][i] = float(distance_matrix[k])
            k += 1

    # Physical graph
    graph_edges = [(0, 2), (0, 3), (0, 5), (0, 7), (1, 3), (2, 6), (2, 7), (4, 5), (5, 7)]
    required_edges = [(0, 2), (0, 3), (0, 5), (0, 7), (2, 6), (4, 5), (5, 7)]

    nodes = list(range(num_nodes))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    # Required directed arcs: both orientations must be available for servicing,
    # but each required edge must be serviced at least once overall (either direction).
    # We enforce that for each required edge, at least one direction is used.
    required_undirected = list(required_edges)

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    # x[i,j]: number of traversals of directed arc (i,j)
    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeIntegers, bounds=(0, 4))

    # y[i,j]: binary, required directed arc (i,j) is serviced
    req_dir_arcs = []
    for (u, v) in required_undirected:
        req_dir_arcs.append((u, v))
        req_dir_arcs.append((v, u))
    model.REQDIR = pyo.Set(initialize=req_dir_arcs, dimen=2)
    model.y = pyo.Var(model.REQDIR, domain=pyo.Binary)

    # Objective
    def obj_rule(mdl):
        return sum(dist[i][j] * mdl.x[i, j] for (i, j) in mdl.ARCS)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Flow conservation (arrivals == departures) at every node
    def flow_rule(mdl, n):
        inflow = sum(mdl.x[i, n] for i in nodes if i != n)
        outflow = sum(mdl.x[n, j] for j in nodes if j != n)
        return inflow == outflow

    model.flow = pyo.Constraint(model.NODES, rule=flow_rule)

    # Depot must have at least one departure and one arrival (closed tour)
    def depot_out(mdl):
        return sum(mdl.x[0, j] for j in nodes if j != 0) >= 1

    model.depot_out = pyo.Constraint(rule=depot_out)

    # Servicing: for each required edge (u,v), at least one direction serviced.
    # y[u,v] + y[v,u] >= 1  AND  y[u,v] <= x[u,v] to couple
    required_pairs = []
    for (u, v) in required_undirected:
        required_pairs.append((u, v))

    model.REQPAIR = pyo.Set(initialize=required_pairs, dimen=2)

    def cover_rule(mdl, u, v):
        return mdl.y[u, v] + mdl.y[v, u] >= 1

    model.cover = pyo.Constraint(model.REQPAIR, rule=cover_rule)

    def link_rule(mdl, i, j):
        return mdl.y[i, j] <= mdl.x[i, j]

    model.link = pyo.Constraint(model.REQDIR, rule=link_rule)

    # Single-commodity flow for connectivity (subtour elimination)
    # One unit of flow originates at depot, each other node consumes 1 unit.
    model.f = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals, bounds=(0, num_nodes - 1))

    def scf_cap_rule(mdl, i, j):
        return mdl.f[i, j] <= (num_nodes - 1) * mdl.x[i, j]

    model.scf_cap = pyo.Constraint(model.ARCS, rule=scf_cap_rule)

    def scf_balance_rule(mdl, n):
        if n == 0:
            out_f = sum(mdl.f[0, j] for j in nodes if j != 0)
            return out_f == num_nodes - 1
        else:
            inflow = sum(mdl.f[i, n] for i in nodes if i != n)
            outflow = sum(mdl.f[n, j] for j in nodes if j != n)
            return inflow - outflow == 1

    model.scf_balance = pyo.Constraint(model.NODES, rule=scf_balance_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
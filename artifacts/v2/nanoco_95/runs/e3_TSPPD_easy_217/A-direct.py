import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    pairs = params["pickup_delivery_pairs"]
    n = params["num_nodes"]
    num_pairs = params["num_pairs"]

    nodes = list(range(n))
    # Nodes to visit (all except hub) plus return to hub creates tour of n positions
    # We model positions 0..n (0 = start/end hub), visiting each non-hub node exactly once.
    positions = list(range(n + 1))  # n+1 positions: hub start (0), n-1 intermediate? 
    # Actually route: start at 0, visit all n-1 other nodes, return to 0 => n arcs, n+1 position slots.

    model = pyo.ConcreteModel()

    n_pos = n  # number of arcs / transitions; positions 0..n (n+1 slots), slot 0 and slot n are hub
    model.P = pyo.RangeSet(0, n_pos)        # position slots 0..n
    model.N = pyo.RangeSet(0, n - 1)        # nodes 0..n-1

    # x[i,j,k] = node j occupied at position k? Better: assignment node->position
    # Let y[k, i] = 1 if node i is visited at position k
    model.y = pyo.Var(model.P, model.N, domain=pyo.Binary)

    # Fix hub at start and end positions
    model.c_hub_start = pyo.Constraint(expr=model.y[0, 0] == 1)
    model.c_hub_end = pyo.Constraint(expr=model.y[n_pos, 0] == 1)

    # Each intermediate position gets exactly one non-hub node
    def intermediate_rule(m, k):
        if k == 0 or k == n_pos:
            return pyo.Constraint.Skip
        return sum(m.y[k, i] for i in m.N if i != 0) == 1
    model.c_intermediate = pyo.Constraint(model.P, rule=intermediate_rule)

    # Hub not placed at intermediate positions
    def hub_intermediate_rule(m, k):
        if k == 0 or k == n_pos:
            return pyo.Constraint.Skip
        return m.y[k, 0] == 0
    model.c_hub_inter = pyo.Constraint(model.P, rule=hub_intermediate_rule)

    # Each non-hub node visited exactly once across intermediate positions
    def node_once_rule(m, i):
        if i == 0:
            return pyo.Constraint.Skip
        return sum(m.y[k, i] for k in m.P if k != 0 and k != n_pos) == 1
    model.c_node_once = pyo.Constraint(model.N, rule=node_once_rule)

    # Precedence: pickup before delivery
    def position_of(m, i):
        # position index where node i is placed
        return sum(k * m.y[k, i] for k in m.P)

    # We need linear precedence. Introduce pos variable.
    model.pos = pyo.Var(model.N, domain=pyo.NonNegativeReals)
    def pos_link_rule(m, k, i):
        return m.pos[i] >= k * m.y[k, i]
    # pos[i] >= sum k*y[k,i] and <= ... since exactly one y, pos = that k. Use big-M style upper bound.
    def pos_upper_rule(m, i):
        return m.pos[i] <= sum(k * m.y[k, i] for k in m.P)
    # Combining: pos[i] equals the position. Enforce pos[i] == sum k*y[k,i]
    model.c_pos_def = pyo.Constraint(model.N, rule=lambda m, i: m.pos[i] == sum(k * m.y[k, i] for k in m.P))

    precedence_cons = []
    for idx, (p, d) in enumerate(pairs):
        pc = pyo.Constraint(expr=model.pos[p] + 1 <= model.pos[d])
        precedence_cons.append(pc)
    model.c_precedence = pyo.ConstraintList()
    for (p, d) in pairs:
        model.c_precedence.add(model.pos[p] + 1 <= model.pos[d])

    # Objective: transition cost from position k node to position k+1 node
    def arc_cost(m, k):
        return sum(
            dist[i][j] * m.y[k, i] * m.y[k + 1, j]
            for i in m.N for j in m.N
        )
    # Quadratic -> linearize with z[k,i,j]
    model.z = pyo.Var([(k, i, j) for k in range(n_pos) for i in nodes for j in nodes], domain=pyo.Binary)
    def z_link1(m, k, i, j):
        return m.z[k, i, j] <= m.y[k, i]
    def z_link2(m, k, i, j):
        return m.z[k, i, j] <= m.y[k + 1, j]
    def z_link3(m, k, i, j):
        return m.z[k, i, j] >= m.y[k, i] + m.y[k + 1, j] - 1

    model.c_z1 = pyo.Constraint([(k, i, j) for k in range(n_pos) for i in nodes for j in nodes], rule=z_link1)
    model.c_z2 = pyo.Constraint([(k, i, j) for k in range(n_pos) for i in nodes for j in nodes], rule=z_link2)
    model.c_z3 = pyo.Constraint([(k, i, j) for k in range(n_pos) for i in nodes for j in nodes], rule=z_link3)

    def obj_rule(m):
        return sum(dist[i][j] * m.z[k, i, j] for k in range(n_pos) for i in nodes for j in nodes)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
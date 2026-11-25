import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    mandatory = params["mandatory_segments"]
    n = params["num_nodes"]
    depot = params["depot"]

    nodes = list(range(n))
    # Directed arc set built from undirected distance matrix
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    # Mandatory segments as undirected pairs; model both directions
    mand_pairs = [(int(a), int(b)) for (a, b) in mandatory]

    model = pyo.ConcreteModel()

    # x[i,j] = number of times the vehicle traverses arc (i,j)
    model.x = pyo.Var(arcs, domain=pyo.NonNegativeIntegers)

    # y[i,j] binary: usage of arc (only meaningful for mandatory arcs)
    mand_arcs = []
    for (a, b) in mand_pairs:
        mand_arcs.append((a, b))
        mand_arcs.append((b, a))
    model.y = pyo.Var(mand_arcs, domain=pyo.Binary)

    # Objective: minimize total distance
    model.cost = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Flow balance at every node (single vehicle, depot start/end)
    def balance_rule(m, k):
        out_ = sum(m.x[k, j] for j in nodes if j != k)
        in_ = sum(m.x[i, k] for i in nodes if i != k)
        return out_ - in_ == 0
    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    # Mandatory segment coverage: sum of traversals in both directions >= 1
    def mand_rule(m, idx):
        a, b = mand_pairs[idx]
        return m.x[a, b] + m.x[b, a] >= 1
    model.mand = pyo.Constraint(range(len(mand_pairs)), rule=mand_rule)

    # Connectivity for mandatory arcs: y[a,b] <= x[a,b] linking
    def link_rule(m, a, b):
        return m.y[a, b] <= m.x[a, b]
    model.link = pyo.Constraint(mand_arcs, rule=link_rule)

    # Depot must be active (at least one outgoing traversal)
    def depot_rule(m):
        return sum(m.x[depot, j] for j in nodes if j != depot) >= 1
    model.depot_min = pyo.Constraint(rule=depot_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}
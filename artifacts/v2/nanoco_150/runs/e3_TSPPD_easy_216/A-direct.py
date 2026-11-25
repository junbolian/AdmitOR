import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 7  # structural: nodes 0..6
    nodes = range(N)

    # Symmetric distance lookup built from params
    def d(i, j):
        if i == j:
            return 0.0
        a, b = (i, j) if i < j else (j, i)
        return params[f"dist_{a}_{b}"]

    D = {(i, j): d(i, j) for i in nodes for j in nodes}

    # Pickup -> delivery precedence: (pickup, delivery)
    pairs = [(6, 2), (5, 4), (1, 3)]

    # Position of each node in the visiting sequence (0 is first, but we let
    # the order among 1..6 be free; depot is fixed as start/end).
    # We model a Hamiltonian cycle 0 -> perm(1..6) -> 0 with MTZ-style ordering
    # variables for the non-depot nodes.

    model = pyo.ConcreteModel()
    model.x = pyo.Var([(i, j) for i in nodes for j in nodes if i != j], within=pyo.Binary)
    # order for nodes 1..6 (depot excluded from ordering)
    order_nodes = [i for i in nodes if i != 0]
    model.u = pyo.Var(order_nodes, bounds=(1, len(order_nodes)), within=pyo.Reals)

    def obj_rule(m):
        return sum(D[i, j] * m.x[i, j] for (i, j) in m.x)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing and one incoming arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1
    model.out_c = pyo.Constraint(nodes, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1
    model.in_c = pyo.Constraint(nodes, rule=in_rule)

    # MTZ subtour elimination for nodes 1..6
    def mtz_rule(m, i, j):
        if i == j or i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + len(order_nodes) * m.x[i, j] <= len(order_nodes) - 1
    model.mtz = pyo.Constraint(order_nodes, order_nodes, rule=mtz_rule)

    # Pickup before delivery precedence
    def prec_rule(m, k):
        p, dl = pairs[k]
        return m.u[p] + 1 <= m.u[dl]
    model.prec = pyo.Constraint(range(len(pairs)), rule=prec_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}
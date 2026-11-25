import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = params["num_nodes"]
    pairs = params["pickup_delivery_pairs"]

    depot = 0
    branches = list(range(1, n))

    # Build model: single continuous Hamiltonian cycle from depot.
    # Use MTZ-style position ordering to embed the sequence and distance.
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(n))
    model.branches = pyo.Set(initialize=branches, ordered=True)

    # x[i,j] = 1 if arc i->j is used
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in range(n) for j in range(n) if i != j],
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # position (order) of each branch visit in the sequence, 1..num_branches
    model.pos = pyo.Var(model.branches, domain=pyo.NonNegativeReals,
                        bounds=(1, len(branches)))

    # Each branch has exactly one incoming and one outgoing arc
    model.in_flow = pyo.Constraint(
        model.branches,
        rule=lambda model_, j: sum(model_.x[i, j] for i in range(n) if i != j) == 1,
    )
    model.out_flow = pyo.Constraint(
        model.branches,
        rule=lambda model_, i: sum(model_.x[i, j] for j in range(n) if j != i) == 1,
    )
    # Depot: one departure and one arrival
    model.depot_out = pyo.Constraint(
        expr=sum(model.x[depot, j] for j in branches) == 1,
    )
    model.depot_in = pyo.Constraint(
        expr=sum(model.x[i, depot] for i in branches) == 1,
    )

    # MTZ subtour elimination: for branch-branch arcs
    model.mtz = pyo.Constraint(
        [(i, j) for i in branches for j in branches if i != j],
        rule=lambda model_, i, j: model_.pos[j] >= model_.pos[i] + 1
        - len(branches) * (1 - model_.x[i, j]),
    )

    # Precedence constraints: pos[pickup] before pos[delivery]
    def _prec_rule(model_, k):
        u, v = pairs[k]
        return model_.pos[v] >= model_.pos[u] + 1

    model.prec = pyo.Constraint(range(len(pairs)), rule=_prec_rule)

    # Objective: total travel distance of the cycle
    model.total_distance = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for (i, j) in model.arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}
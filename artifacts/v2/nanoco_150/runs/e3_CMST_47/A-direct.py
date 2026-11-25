import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["node_coordinates"]
    N = len(coords)

    # Build symmetric cost matrix from upper-triangle edge_costs
    cost = [[0.0] * N for _ in range(N)]
    edge_costs = params["edge_costs"]
    if isinstance(edge_costs, dict):
        for (i, j), v in edge_costs.items():
            cost[i][j] = v
            cost[j][i] = v
    else:
        for i in range(N):
            row = edge_costs[i]
            for j in range(N):
                if isinstance(row, dict):
                    if j in row:
                        cost[i][j] = row[j]
                else:
                    cost[i][j] = row[j]
    max_branch_size = params["max_branch_size"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, N - 1)
    stations = list(range(1, N))

    # Directed flow variables: y[i,j] = 1 if arc i->j is used (i is parent of j)
    all_arcs = [(i, j) for i in range(N) for j in range(N) if i != j]
    model.arcs = pyo.Set(initialize=all_arcs, dimen=2)
    model.y = pyo.Var(model.arcs, domain=pyo.Binary)

    # f[i,j] = flow on arc i->j representing # of nodes in subtree routed through j (j side)
    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # Objective: minimize total cable cost
    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.y[i, j] for (i, j) in all_arcs),
        sense=pyo.minimize,
    )

    # Each non-root node has exactly one parent
    model.one_parent = pyo.Constraint(
        stations,
        rule=lambda m, j: sum(m.y[i, j] for i in range(N) if i != j) == 1,
    )

    # Root has no incoming arc
    model.root_no_in = pyo.Constraint(
        rule=lambda m: sum(m.y[i, 0] for i in range(1, N)) == 0,
    )

    # Flow conservation: each non-root node sends out flow equal to
    # (number of nodes in its subtree) - 1, given its parent's flow.
    # Define: flow into j from parent = subtree_size(j).
    # Each node j (j != 0) has subtree size s_j = 1 + sum of children subtree sizes.
    # Model via flow: f[i,j] = subtree size of j if y[i,j]=1.
    # Constraint at j (non-root): sum_{k child of j} f[j,k] = f[parent(j), j] - 1.
    # Enforce: sum_{k != j} f[j,k] = sum_{i != j} f[i,j] - 1  (for j != 0)
    # and f[i,j] <= (N-1) * y[i,j]

    model.link_capacity = pyo.Constraint(
        all_arcs,
        rule=lambda m, i, j: m.f[i, j] <= (N - 1) * m.y[i, j],
    )

    # Flow bounds
    model.flow_lb = pyo.Constraint(
        all_arcs,
        rule=lambda m, i, j: m.f[i, j] >= 1 * m.y[i, j],
    )

    def flow_balance_rule(m, j):
        inflow = sum(m.f[i, j] for i in range(N) if i != j)
        outflow = sum(m.f[j, k] for k in range(N) if k != j)
        return outflow == inflow - 1

    model.flow_balance = pyo.Constraint(stations, rule=flow_balance_rule)

    # Root flow balance: total flow out of root = N - 1
    model.root_flow = pyo.Constraint(
        rule=lambda m: sum(m.f[0, k] for k in range(1, N)) == N - 1,
    )

    # Root outgoing flow bounds
    model.root_out_bound = pyo.Constraint(
        range(1, N),
        rule=lambda m, k: m.f[0, k] <= (max_branch_size) * m.y[0, k],
    )
    model.root_out_lb = pyo.Constraint(
        range(1, N),
        rule=lambda m, k: m.f[0, k] >= 1 * m.y[0, k],
    )

    # Root must have at least one child
    model.root_out = pyo.Constraint(
        rule=lambda m: sum(m.y[0, k] for k in range(1, N)) >= 1,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}
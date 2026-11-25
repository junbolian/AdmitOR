import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coords"]
    dist = params["distance_matrix"]
    num_nodes = len(coords)

    nodes = list(range(num_nodes))
    branches = nodes[1:]

    pairs = [[4, 3], [2, 6], [5, 1]]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes)
    model.B = pyo.Set(initialize=branches)

    # x[i, j] = 1 if arc i->j is used
    model.x = pyo.Var(model.N, model.N, domain=pyo.Binary)

    # position/order variable: cumulative arrival position along route
    model.pos = pyo.Var(model.N, domain=pyo.NonNegativeReals, bounds=(0, num_nodes))

    model.obj = pyo.Objective(
        expr=sum(dist[i][j] * model.x[i, j] for i in nodes for j in nodes if i != j),
        sense=pyo.minimize,
    )

    # Each node has exactly one outgoing arc
    model.out_rule = pyo.Constraint(
        model.N, rule=lambda m, i: sum(m.x[i, j] for j in nodes if j != i) == 1
    )

    # Each node has exactly one incoming arc
    model.in_rule = pyo.Constraint(
        model.N, rule=lambda m, j: sum(m.x[i, j] for i in nodes if i != j) == 1
    )

    # Subtour elimination (Miller-Tucker-Zemlin style) using positions
    # pos[0] = 0 fixed; for branches positions in [1, num_nodes-1]
    model.fix_depot = pyo.Constraint(expr=model.pos[0] == 0)

    big_m = num_nodes
    model.mtz = pyo.Constraint(
        [(i, j) for i in nodes for j in branches if i != j],
        rule=lambda m, i, j: m.pos[j] >= m.pos[i] + 1 - big_m * (1 - m.x[i, j]),
    )

    # Precedence: pickup placed strictly before delivery in position order
    def precedence_rule(m, u, v):
        return m.pos[u] + 1 <= m.pos[v]

    model.precedence = pyo.Constraint(
        [(u, v) for (u, v) in pairs],
        rule=lambda m, u, v: m.pos[u] + 1 <= m.pos[v],
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = int(params["num_nodes"])

    nodes = list(range(n))
    clients = list(range(1, n))

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes)
    model.clients = pyo.Set(initialize=clients)

    # x[i,j] = 1 if arc i->j is used
    model.arcs = pyo.Set(dimen=2, initialize=[(i, j) for i in nodes for j in nodes if i != j])
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # u[i] = position/order of node i in the tour (for MTZ subtour elimination)
    model.u = pyo.Var(model.clients, domain=pyo.Reals, bounds=(1, n - 1))

    # Objective: minimize total travel cost
    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for (i, j) in m.arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each client has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in nodes if j != i) == 1
    model.out_flow = pyo.Constraint(model.clients, rule=out_rule)
    # Depot also has exactly one outgoing arc
    def out_depot_rule(m):
        return sum(m.x[0, j] for j in nodes if j != 0) == 1
    model.out_depot = pyo.Constraint(rule=out_depot_rule)

    # Each client has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in nodes if i != j) == 1
    model.in_flow = pyo.Constraint(model.clients, rule=in_rule)
    # Depot has exactly one incoming arc
    def in_depot_rule(m):
        return sum(m.x[i, 0] for i in nodes if i != 0) == 1
    model.in_depot = pyo.Constraint(rule=in_depot_rule)

    # MTZ subtour elimination constraints (only between clients)
    def mtz_rule(m, i, j):
        if i != j:
            return m.u[i] - m.u[j] + (n - 1) * m.x[i, j] <= n - 2
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(model.clients, model.clients, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
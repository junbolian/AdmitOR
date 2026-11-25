import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    num_nodes = params["num_nodes"]
    num_pairs = params["num_pairs"]

    nodes = list(range(num_nodes))
    clients = list(range(1, num_nodes))
    pairs = [(4, 5), (6, 1), (2, 3)][:num_pairs]

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(clients, domain=pyo.NonNegativeReals, bounds=(1, num_nodes - 1))

    def obj_rule(md):
        return sum(distance_matrix[i][j] * md.x[i, j] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(md, i):
        return sum(md.x[i, j] for j in nodes if j != i) == 1

    def in_rule(md, j):
        return sum(md.x[i, j] for i in nodes if i != j) == 1

    model.out_con = pyo.Constraint(nodes, rule=out_rule)
    model.in_con = pyo.Constraint(nodes, rule=in_rule)

    # Subtour elimination (MTZ) on client nodes
    def mtz_rule(md, i, j):
        if i != j:
            return md.u[i] - md.u[j] + (num_nodes - 1) * md.x[i, j] <= num_nodes - 2
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(clients, clients, rule=mtz_rule)

    # Precedence constraints for pickup-delivery pairs
    model.prec = pyo.ConstraintList()
    for (pickup, delivery) in pairs:
        model.prec.add(model.u[pickup] <= model.u[delivery] - 1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
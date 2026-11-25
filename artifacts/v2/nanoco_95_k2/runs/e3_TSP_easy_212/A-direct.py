import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    distance_matrix = params["distance_matrix"]

    nodes = list(range(num_nodes))

    model = pyo.ConcreteModel()

    # Decision variables: x[i, j] = 1 if truck travels directly from i to j
    model.x = pyo.Var(nodes, nodes, domain=pyo.Binary)

    # MTZ auxiliary variables: order/position of each node in the tour
    model.u = pyo.Var(nodes, domain=pyo.NonNegativeReals, bounds=(1, num_nodes - 1))

    # Objective: minimize total travel distance
    model.obj = pyo.Objective(
        expr=sum(distance_matrix[i][j] * model.x[i, j]
                 for i in nodes for j in nodes if i != j),
        sense=pyo.minimize,
    )

    # Each node has exactly one outgoing arc
    model.out_arc = pyo.Constraint(
        nodes,
        rule=lambda m, i: sum(m.x[i, j] for j in nodes if j != i) == 1,
    )

    # Each node has exactly one incoming arc
    model.in_arc = pyo.Constraint(
        nodes,
        rule=lambda m, j: sum(m.x[i, j] for i in nodes if i != j) == 1,
    )

    # Subtour elimination (MTZ) for customer nodes 1..num_nodes-1
    customers = list(range(1, num_nodes))

    def mtz_rule(m, i, j):
        if i != j:
            return m.u[i] - m.u[j] + (num_nodes - 1) * m.x[i, j] <= num_nodes - 2
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(customers, customers, rule=mtz_rule)

    # Solve with HiGHS via Appsi
    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
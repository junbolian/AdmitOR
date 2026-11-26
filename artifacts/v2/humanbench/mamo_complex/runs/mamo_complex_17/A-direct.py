import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]
    num_centers = int(params["num_centers"])
    source_node = int(params["source_node"])
    sink_node = int(params["sink_node"])

    nodes = list(range(num_centers))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def cap(i, j):
        try:
            return float(capacity_matrix[i][j])
        except (IndexError, TypeError):
            return 0.0

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # Capacity constraints
    model.cap_con = pyo.Constraint(
        model.arcs,
        rule=lambda m, i, j: m.flow[i, j] <= cap(i, j),
    )

    # Flow conservation at intermediate nodes (not source, not sink)
    def conservation_rule(m, k):
        if k == source_node or k == sink_node:
            return pyo.Constraint.Skip
        inflow = sum(m.flow[i, k] for i in nodes if i != k)
        outflow = sum(m.flow[k, j] for j in nodes if j != k)
        return inflow == outflow

    model.cons = pyo.Constraint(model.nodes, rule=conservation_rule)

    # Objective: maximize net outflow from source (equivalently inflow to sink)
    def obj_rule(m):
        return sum(m.flow[source_node, j] for j in nodes if j != source_node)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}
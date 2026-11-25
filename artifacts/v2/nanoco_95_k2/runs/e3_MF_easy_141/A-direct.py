import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]
    source_node = params["source_node"]
    sink_node = params["sink_node"]

    arcs = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6),
        (3, 4), (3, 8), (3, 9), (4, 5), (4, 8),
        (5, 6), (6, 7), (7, 8), (7, 9), (8, 9),
    ]

    model = pyo.ConcreteModel()

    model.arc_set = pyo.Set(initialize=range(num_arcs), ordered=True)
    model.node_set = pyo.Set(initialize=range(num_nodes), ordered=True)

    def cap_rule(m, a):
        return (0.0, capacities[a])

    model.flow = pyo.Var(model.arc_set, bounds=cap_rule)

    # net outflow auxiliary for cost-min objective at max flow
    def obj_rule(m):
        return sum(costs[a] * m.flow[a] for a in m.arc_set)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def conservation_rule(m, n):
        if n == source_node or n == sink_node:
            return pyo.Constraint.Skip
        inflow = sum(m.flow[a] for a in m.arc_set if arcs[a][1] == n)
        outflow = sum(m.flow[a] for a in m.arc_set if arcs[a][0] == n)
        return inflow == outflow

    model.conservation = pyo.Constraint(model.node_set, rule=conservation_rule)

    def maxflow_rule(m):
        out_source = sum(m.flow[a] for a in m.arc_set if arcs[a][0] == source_node)
        return out_source

    # Solve lexicographically: first maximize flow, then minimize cost.
    # Do this via two sequential solves on the same model.
    model.max_flow_expr = pyo.Expression(rule=maxflow_rule)

    # Phase 1: maximize flow
    model.obj_maxflow = pyo.Objective(expr=model.max_flow_expr, sense=pyo.maximize)
    model.total_cost.deactivate()

    solver = Highs()
    solver.solve(model)

    max_flow_val = pyo.value(model.max_flow_expr)

    # Fix flow to the maximum value
    model.flow_fix = pyo.Constraint(expr=model.max_flow_expr == max_flow_val)

    # Phase 2: minimize cost subject to max flow
    model.obj_maxflow.deactivate()
    model.total_cost.activate()

    solver2 = Highs()
    solver2.solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}
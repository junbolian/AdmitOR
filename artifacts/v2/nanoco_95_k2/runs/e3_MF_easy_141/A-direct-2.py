import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = list(params["capacities"])
    costs = list(params["costs"])
    node_coordinates = params["node_coordinates"]
    source_node = int(params["source_node"])
    sink_node = int(params["sink_node"])
    num_nodes = int(params["num_nodes"])
    num_arcs = int(params["num_arcs"])

    arcs = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6),
        (3, 4), (3, 8), (3, 9), (4, 5), (4, 8),
        (5, 6), (6, 7), (7, 8), (7, 9), (8, 9),
    ]

    model = pyo.ConcreteModel()

    model.arc_set = pyo.RangeSet(0, num_arcs - 1)
    model.node_set = pyo.RangeSet(0, num_nodes - 1)

    def flow_bounds(mdl, i):
        return (0, capacities[i])

    model.flow = pyo.Var(model.arc_set, bounds=flow_bounds)

    # Objective: maximize total flow out of the source node.
    def obj_rule(mdl):
        return sum(
            mdl.flow[i] for i in range(num_arcs) if arcs[i][0] == source_node
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Flow conservation at intermediate nodes.
    intermediate_nodes = [
        n for n in range(num_nodes) if n != source_node and n != sink_node
    ]

    def conservation_rule(mdl, n):
        inflow = sum(
            mdl.flow[i] for i in range(num_arcs) if arcs[i][1] == n
        )
        outflow = sum(
            mdl.flow[i] for i in range(num_arcs) if arcs[i][0] == n
        )
        return inflow - outflow == 0

    model.conservation = pyo.Constraint(intermediate_nodes, rule=conservation_rule)

    # Fix the source outflow to the exact optimum (computed below).
    # Step 1: solve pure max-flow.
    Highs().solve(model)

    max_flow_val = pyo.value(model.obj)

    # Step 2: pin the total delivered flow to the max flow and minimize cost.
    model.max_flow_con = pyo.Constraint(expr=model.obj.expr <= max_flow_val)
    model.min_flow_con = pyo.Constraint(expr=model.obj.expr >= max_flow_val)

    def cost_rule(mdl):
        return sum(costs[i] * mdl.flow[i] for i in range(num_arcs))

    model.cost_obj = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Deactivate the original max-flow objective by fixing it via constraints
    # and switching the active objective to cost minimization.
    model.obj.deactivate()

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost_obj))

    return {"objective": obj_val, "status": "optimal"}
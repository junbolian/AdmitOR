# IR: {"sets":{"nodes":[1,2,3,4],"edges":[[1,2],[1,3],[2,3],[2,4],[3,4]],"intermediate_nodes":[2,3]},"params":{"capacity_1_2":"capacity of (1,2)","capacity_1_3":"capacity of (1,3)","capacity_2_3":"capacity of (2,3)","capacity_2_4":"capacity of (2,4)","capacity_3_4":"capacity of (3,4)"},"variables":{"flow[i,j]":"nonnegative continuous for each edge"},"constraints":["flow[i,j] <= capacity[i,j] for each edge","sum(flow[i,v] for incoming edges) = sum(flow[v,j] for outgoing edges) for each intermediate node v"],"objective":"maximize flow[1,2] + flow[1,3]","reporting":"return objective rounded to the nearest integer as a float"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = {
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 3): params["capacity_2_3"],
        (2, 4): params["capacity_2_4"],
        (3, 4): params["capacity_3_4"],
    }

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=[1, 2, 3, 4])
    model.edges = pyo.Set(dimen=2, initialize=list(capacities))
    model.intermediate_nodes = pyo.Set(initialize=[2, 3])

    model.capacity = pyo.Param(
        model.edges,
        initialize=capacities,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def capacity_rule(instance, source, target):
        return instance.flow[source, target] <= instance.capacity[source, target]

    model.capacity_limits = pyo.Constraint(
        model.edges,
        rule=capacity_rule,
    )

    def conservation_rule(instance, node):
        incoming = sum(
            instance.flow[source, target]
            for source, target in instance.edges
            if target == node
        )
        outgoing = sum(
            instance.flow[source, target]
            for source, target in instance.edges
            if source == node
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=model.flow[1, 2] + model.flow[1, 3],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}
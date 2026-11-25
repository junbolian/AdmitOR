# IR: {"sets":{"N":[0,1,2,3,4,5],"A":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]]},"params":{"supply":"[supply_0,supply_1,supply_2,supply_3,-demand_4,-demand_5]","coord_x":"coord_x indexed by N; geographic metadata","coord_y":"coord_y indexed by N; geographic metadata","capacity":"capacity indexed by position in A","unit_cost":"unit_cost indexed by position in A"},"variables":{"flow[i,j]":"nonnegative continuous, (i,j) in A"},"constraints":["balance[n]: sum(flow[n,j]) - sum(flow[i,n]) = supply[n], n in N","arc_capacity[i,j]: flow[i,j] <= capacity[i,j], (i,j) in A"],"objective":"minimize sum(unit_cost[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    arcs = (
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 4),
        (2, 5),
        (3, 4),
        (3, 5),
        (0, 4),
        (0, 5),
        (1, 4),
        (1, 5),
    )

    supply_data = {
        0: params["supply_0"],
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: -params["demand_4"],
        5: -params["demand_5"],
    }
    coord_x_data = params["coord_x"]
    coord_y_data = params["coord_y"]
    capacity_data = params["capacity"]
    unit_cost_data = params["unit_cost"]

    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(
        dimen=2, initialize=arcs, ordered=True, within=model.nodes * model.nodes
    )

    model.supply = pyo.Param(
        model.nodes, initialize=supply_data, within=pyo.Reals
    )
    model.coord_x = pyo.Param(
        model.nodes,
        initialize={node: coord_x_data[node] for node in nodes},
        within=pyo.Reals,
    )
    model.coord_y = pyo.Param(
        model.nodes,
        initialize={node: coord_y_data[node] for node in nodes},
        within=pyo.Reals,
    )
    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: capacity_data[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: unit_cost_data[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(instance, node):
        return (
            sum(instance.flow[arc] for arc in outgoing[node])
            - sum(instance.flow[arc] for arc in incoming[node])
            == instance.supply[node]
        )

    model.node_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def capacity_rule(instance, origin, destination):
        return (
            instance.flow[origin, destination]
            <= instance.arc_capacity[origin, destination]
        )

    model.capacity_limit = pyo.Constraint(model.arcs, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[arc] * model.flow[arc]
            for arc in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
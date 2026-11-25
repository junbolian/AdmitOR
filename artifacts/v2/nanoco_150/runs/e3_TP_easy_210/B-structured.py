# IR: {"sets":{"F":[0,1,2],"T":[3,4,5,6],"A":[[0,3],[0,4],[0,5],[0,6],[1,3],[1,4],[1,5],[1,6],[2,3],[2,4],[2,5],[2,6]]},"params":{"supply":"params['supply'][i], i in F","demand":"params['demand'][j-3], j in T; positive requirements","cost":"params['cost'][k], k indexes A in listed order","capacity":"params['capacity'][k], k indexes A in listed order"},"variables":{"flow[i,j]":"continuous, nonnegative; (i,j) in A"},"constraints":["sum(flow[i,j] for j in T) == supply[i], for i in F","sum(flow[i,j] for i in F) == demand[j], for j in T","flow[i,j] <= capacity[i,j], for (i,j) in A"],"objective":"minimize sum(cost[i,j] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fabrication_nodes = (0, 1, 2)
    testing_nodes = (3, 4, 5, 6)
    arcs = tuple(
        (source, destination)
        for source in fabrication_nodes
        for destination in testing_nodes
    )

    model = pyo.ConcreteModel()

    model.fabrication_nodes = pyo.Set(
        initialize=fabrication_nodes, ordered=True
    )
    model.testing_nodes = pyo.Set(
        initialize=testing_nodes, ordered=True
    )
    model.transport_arcs = pyo.Set(
        dimen=2, initialize=arcs, ordered=True
    )

    model.source_supply = pyo.Param(
        model.fabrication_nodes,
        initialize={
            source: params["supply"][position]
            for position, source in enumerate(fabrication_nodes)
        },
        within=pyo.Reals,
    )
    model.testing_demand = pyo.Param(
        model.testing_nodes,
        initialize={
            destination: params["demand"][position]
            for position, destination in enumerate(testing_nodes)
        },
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.transport_arcs,
        initialize={
            arc: params["cost"][position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.arc_capacity = pyo.Param(
        model.transport_arcs,
        initialize={
            arc: params["capacity"][position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(
        model.transport_arcs, domain=pyo.NonNegativeReals
    )

    def supply_balance_rule(instance, source):
        return (
            sum(
                instance.flow[source, destination]
                for destination in instance.testing_nodes
            )
            == instance.source_supply[source]
        )

    def demand_balance_rule(instance, destination):
        return (
            sum(
                instance.flow[source, destination]
                for source in instance.fabrication_nodes
            )
            == instance.testing_demand[destination]
        )

    def capacity_limit_rule(instance, source, destination):
        return (
            instance.flow[source, destination]
            <= instance.arc_capacity[source, destination]
        )

    model.supply_balance = pyo.Constraint(
        model.fabrication_nodes, rule=supply_balance_rule
    )
    model.demand_balance = pyo.Constraint(
        model.testing_nodes, rule=demand_balance_rule
    )
    model.capacity_limit = pyo.Constraint(
        model.transport_arcs, rule=capacity_limit_rule
    )

    model.shipping_objective = pyo.Objective(
        expr=sum(
            model.shipping_cost[source, destination]
            * model.flow[source, destination]
            for source, destination in model.transport_arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.shipping_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
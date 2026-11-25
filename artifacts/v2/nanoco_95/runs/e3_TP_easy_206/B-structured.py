# IR: {"sets":{"S":[0,1,2],"D":[3,4,5,6],"A":"S x D, ordered by supply node then clinic"},"params":{"supply":"params['supply'][i], i in S","demand":"params['demand'][j-3], j in D","arc_capacity":"params['arc_capacity'][4*i+j-3], (i,j) in A","arc_cost":"params['arc_cost'][4*i+j-3], (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative, (i,j) in A"},"constraints":["sum(flow[i,j] for j in D) == supply[i] for i in S","sum(flow[i,j] for i in S) == demand[j] for j in D","flow[i,j] <= arc_capacity[i,j] for (i,j) in A"],"objective":"minimize sum(arc_cost[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Inputs are sequences; demand is ordered by clinics 3, 4, 5, 6."""
    supply_data = params["supply"]
    demand_data = params["demand"]
    capacity_data = params["arc_capacity"]
    cost_data = params["arc_cost"]

    model = pyo.ConcreteModel()

    model.supply_nodes = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.clinic_nodes = pyo.Set(initialize=[3, 4, 5, 6], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (source, clinic)
            for source in model.supply_nodes
            for clinic in model.clinic_nodes
        ],
        ordered=True,
    )

    model.supply = pyo.Param(
        model.supply_nodes,
        initialize={source: supply_data[source] for source in model.supply_nodes},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.clinic_nodes,
        initialize={
            clinic: demand_data[clinic - 3]
            for clinic in model.clinic_nodes
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize={
            (source, clinic): capacity_data[4 * source + clinic - 3]
            for source, clinic in model.arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={
            (source, clinic): cost_data[4 * source + clinic - 3]
            for source, clinic in model.arcs
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def supply_balance_rule(network, source):
        return (
            sum(network.flow[source, clinic] for clinic in network.clinic_nodes)
            == network.supply[source]
        )

    model.supply_balance = pyo.Constraint(
        model.supply_nodes, rule=supply_balance_rule
    )

    def demand_balance_rule(network, clinic):
        return (
            sum(network.flow[source, clinic] for source in network.supply_nodes)
            == network.demand[clinic]
        )

    model.demand_balance = pyo.Constraint(
        model.clinic_nodes, rule=demand_balance_rule
    )

    def corridor_limit_rule(network, source, clinic):
        return (
            network.flow[source, clinic]
            <= network.arc_capacity[source, clinic]
        )

    model.corridor_limit = pyo.Constraint(
        model.arcs, rule=corridor_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[source, clinic] * model.flow[source, clinic]
            for source, clinic in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"N":[0,1,2,3,4,5,6],"F":[0,1,2],"R":[3,4,5,6],"D":[0,1],"A":[[0,3],[0,4],[0,5],[0,6],[1,3],[1,4],[1,5],[1,6],[2,3],[2,4],[2,5],[2,6]]},"params":{"node_coordinates":"N x D real; descriptive metadata","farm_supply":"F nonnegative real","retail_demand":"R nonnegative real; positive required quantities","arc_capacities":"A nonnegative real; supplied in A order","arc_unit_costs":"A real; supplied in A order"},"variables":{"flow[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["sum(flow[i,j] for j in R) == farm_supply[i] for i in F","sum(flow[i,j] for i in F) == retail_demand[j] for j in R","flow[i,j] <= arc_capacities[i,j] for (i,j) in A"],"objective":"minimize sum(arc_unit_costs[i,j] * flow[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Farm supplies and retail demands may be sequences in node order
    or mappings keyed by their corresponding node IDs. Coordinates
    are indexed by node ID, then coordinate index. Arc capacities and
    costs are sequences in the specified arc order.
    """
    nodes = tuple(range(7))
    farms = (0, 1, 2)
    retailers = (3, 4, 5, 6)
    arcs = tuple((farm, retailer) for farm in farms for retailer in retailers)

    coordinates = params["node_coordinates"]
    supplies = params["farm_supply"]
    demands = params["retail_demand"]
    capacities = params["arc_capacities"]
    costs = params["arc_unit_costs"]

    supply_data = {
        farm: supplies[farm] if isinstance(supplies, Mapping) else supplies[position]
        for position, farm in enumerate(farms)
    }
    demand_data = {
        retailer: (
            demands[retailer]
            if isinstance(demands, Mapping)
            else demands[position]
        )
        for position, retailer in enumerate(retailers)
    }

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.F = pyo.Set(initialize=farms, ordered=True)
    model.R = pyo.Set(initialize=retailers, ordered=True)
    model.D = pyo.Set(initialize=(0, 1), ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.node_coordinates = pyo.Param(
        model.N,
        model.D,
        initialize={
            (node, dimension): coordinates[node][dimension]
            for node in nodes
            for dimension in (0, 1)
        },
        within=pyo.Reals,
    )
    model.farm_supply = pyo.Param(
        model.F, initialize=supply_data, within=pyo.NonNegativeReals
    )
    model.retail_demand = pyo.Param(
        model.R, initialize=demand_data, within=pyo.NonNegativeReals
    )
    model.arc_capacities = pyo.Param(
        model.A,
        initialize={arc: capacities[position] for position, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
    )
    model.arc_unit_costs = pyo.Param(
        model.A,
        initialize={arc: costs[position] for position, arc in enumerate(arcs)},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def supply_rule(current_model, farm):
        return (
            sum(current_model.flow[farm, retailer] for retailer in current_model.R)
            == current_model.farm_supply[farm]
        )

    def demand_rule(current_model, retailer):
        return (
            sum(current_model.flow[farm, retailer] for farm in current_model.F)
            == current_model.retail_demand[retailer]
        )

    def capacity_rule(current_model, farm, retailer):
        return (
            current_model.flow[farm, retailer]
            <= current_model.arc_capacities[farm, retailer]
        )

    model.supply_balance = pyo.Constraint(model.F, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.R, rule=demand_rule)
    model.route_capacity = pyo.Constraint(model.A, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_unit_costs[farm, retailer] * model.flow[farm, retailer]
            for farm, retailer in model.A
        ),
        sense=pyo.minimize,
    )

    # APPSI can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines whether a solution is returned.
    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "infeasible_or_failed" if solver_failed else "no_solution",
        }

    return {"objective": obj_val, "status": "optimal"}
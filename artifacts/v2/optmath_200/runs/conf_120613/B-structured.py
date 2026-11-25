# IR (JSON):
# {
#   "sets": {
#     "nodes": [0, 1, 2, 3],
#     "commodities": [1, 2],
#     "arcs": [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 0], [2, 1], [3, 1], [3, 2]],
#     "facility_arcs": [[0, 3], [1, 2], [1, 3], [2, 0], [2, 1], [3, 1], [3, 2]]
#   },
#   "params": {
#     "transport_cost": {
#       "1,0,3": "transport_cost_c1_0_3",
#       "2,1,2": "transport_cost_c2_1_2",
#       "1,0,1": "transport_cost_c1_0_1",
#       "1,0,2": "transport_cost_c1_0_2",
#       "2,1,3": "transport_cost_c2_1_3"
#     },
#     "install_cost": {
#       "0,3": "install_cost_0_3",
#       "1,2": "install_cost_1_2",
#       "1,3": "install_cost_1_3",
#       "2,0": "install_cost_2_0",
#       "2,1": "install_cost_2_1",
#       "3,1": "install_cost_3_1",
#       "3,2": "install_cost_3_2"
#     },
#     "capacity": {
#       "0,3": "capacity_0_3",
#       "1,2": "capacity_1_2",
#       "1,3": "capacity_1_3",
#       "2,0": "capacity_2_0",
#       "2,1": "capacity_2_1",
#       "3,1": "capacity_3_1",
#       "3,2": "capacity_3_2"
#     }
#   },
#   "structural_data": {
#     "origins": {"1": 0, "2": 1},
#     "destinations": {"1": 3, "2": 2},
#     "demand_per_commodity": 1
#   },
#   "interpretation": [
#     "Only listed routes exist; every commodity can use every listed route.",
#     "Unspecified transportation costs are zero.",
#     "Capacity constraints apply only to facility_arcs; arcs 0->1 and 0->2 have no installation requirement.",
#     "Flow conservation follows the stated origins and destinations."
#   ],
#   "variables": {
#     "flow[k,i,j]": "continuous, 0 <= flow <= 1",
#     "facilities[i,j]": "nonnegative integer, indexed by facility_arcs"
#   },
#   "constraints": [
#     "For each commodity k and node v: sum_j flow[k,v,j] - sum_i flow[k,i,v] = 1 if v is origin[k], -1 if v is destination[k], otherwise 0.",
#     "For each facility arc (i,j): sum_k flow[k,i,j] <= capacity[i,j] * facilities[i,j]."
#   ],
#   "objective": "Minimize sum_(k,i,j with specified cost) transport_cost[k,i,j]*flow[k,i,j] + sum_(i,j in facility_arcs) install_cost[i,j]*facilities[i,j]."
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = (0, 1, 2, 3)
    commodities = (1, 2)
    arcs = (
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 0),
        (2, 1),
        (3, 1),
        (3, 2),
    )
    facility_arcs = (
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 0),
        (2, 1),
        (3, 1),
        (3, 2),
    )
    origins = {1: 0, 2: 1}
    destinations = {1: 3, 2: 2}

    transport_costs = {
        (1, 0, 3): params["transport_cost_c1_0_3"],
        (2, 1, 2): params["transport_cost_c2_1_2"],
        (1, 0, 1): params["transport_cost_c1_0_1"],
        (1, 0, 2): params["transport_cost_c1_0_2"],
        (2, 1, 3): params["transport_cost_c2_1_3"],
    }
    installation_costs = {
        (0, 3): params["install_cost_0_3"],
        (1, 2): params["install_cost_1_2"],
        (1, 3): params["install_cost_1_3"],
        (2, 0): params["install_cost_2_0"],
        (2, 1): params["install_cost_2_1"],
        (3, 1): params["install_cost_3_1"],
        (3, 2): params["install_cost_3_2"],
    }
    capacities = {
        (0, 3): params["capacity_0_3"],
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 0): params["capacity_2_0"],
        (2, 1): params["capacity_2_1"],
        (3, 1): params["capacity_3_1"],
        (3, 2): params["capacity_3_2"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.commodities = pyo.Set(initialize=commodities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.facility_arcs = pyo.Set(
        dimen=2, initialize=facility_arcs, ordered=True
    )
    model.costed_flows = pyo.Set(
        dimen=3, initialize=tuple(transport_costs), ordered=True
    )

    model.transport_cost = pyo.Param(
        model.costed_flows, initialize=transport_costs, within=pyo.Reals
    )
    model.install_cost = pyo.Param(
        model.facility_arcs, initialize=installation_costs, within=pyo.Reals
    )
    model.route_capacity = pyo.Param(
        model.facility_arcs, initialize=capacities, within=pyo.Reals
    )

    model.flow = pyo.Var(
        model.commodities,
        model.arcs,
        domain=pyo.NonNegativeReals,
        bounds=(0, 1),
    )
    model.facilities = pyo.Var(
        model.facility_arcs, domain=pyo.NonNegativeIntegers
    )

    def flow_balance_rule(network, commodity, node):
        outgoing = sum(
            network.flow[commodity, tail, head]
            for tail, head in arcs
            if tail == node
        )
        incoming = sum(
            network.flow[commodity, tail, head]
            for tail, head in arcs
            if head == node
        )
        net_supply = (
            1 if node == origins[commodity]
            else -1 if node == destinations[commodity]
            else 0
        )
        return outgoing - incoming == net_supply

    model.flow_balance = pyo.Constraint(
        model.commodities, model.nodes, rule=flow_balance_rule
    )

    def capacity_rule(network, tail, head):
        return (
            sum(
                network.flow[commodity, tail, head]
                for commodity in commodities
            )
            <= network.route_capacity[tail, head]
            * network.facilities[tail, head]
        )

    model.capacity_limits = pyo.Constraint(
        model.facility_arcs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[commodity, tail, head]
            * model.flow[commodity, tail, head]
            for commodity, tail, head in model.costed_flows
        )
        + sum(
            model.install_cost[tail, head] * model.facilities[tail, head]
            for tail, head in facility_arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
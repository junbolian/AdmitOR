# IR:
# {"sets":{"N":[0,1,2,3,4,5,6,7,8,9],"K":[1,2],"E":[[0,1],[0,5],[0,7],[0,8],[0,9],[1,2],[2,3],[2,9],[3,4],[4,5],[5,6],[6,7],[6,9],[7,8],[8,9]],"A":"Both directed orientations of every edge in E"},
# "params":{"capacity":"For each edge suffix in [01_10,05_50,07_70,08_80,09_90,12_21,23_32,29_92,34_43,45_54,56_65,67_76,69_96,78_87,89_98], read params['arc_capacity_'+suffix]; assign to both orientations; nonnegative","unit_cost":"For each corresponding edge suffix, read params['unit_cost_'+suffix]; assign to both orientations; retained as data but unused in this utilization objective","demand":{"1":"params['demand_flow1_5_to_4']","2":"params['demand_flow2_3_to_0']"},"source":{"1":5,"2":3},"destination":{"1":4,"2":0}},
# "variables":{"traffic[k,i,j]":"Nonnegative continuous for k in K and (i,j) in A","peak_utilization":"Continuous in [0,1]"},
# "constraints":["For each k,n: sum_j traffic[k,n,j] - sum_i traffic[k,i,n] = demand[k] at source[k], -demand[k] at destination[k], and 0 otherwise","For each (i,j): sum_k traffic[k,i,j] <= capacity[i,j]","For each (i,j): sum_k traffic[k,i,j] <= peak_utilization * capacity[i,j]"],
# "objective":"Minimize peak_utilization"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_data = [
        (0, 1, params["arc_capacity_01_10"], params["unit_cost_01_10"]),
        (0, 5, params["arc_capacity_05_50"], params["unit_cost_05_50"]),
        (0, 7, params["arc_capacity_07_70"], params["unit_cost_07_70"]),
        (0, 8, params["arc_capacity_08_80"], params["unit_cost_08_80"]),
        (0, 9, params["arc_capacity_09_90"], params["unit_cost_09_90"]),
        (1, 2, params["arc_capacity_12_21"], params["unit_cost_12_21"]),
        (2, 3, params["arc_capacity_23_32"], params["unit_cost_23_32"]),
        (2, 9, params["arc_capacity_29_92"], params["unit_cost_29_92"]),
        (3, 4, params["arc_capacity_34_43"], params["unit_cost_34_43"]),
        (4, 5, params["arc_capacity_45_54"], params["unit_cost_45_54"]),
        (5, 6, params["arc_capacity_56_65"], params["unit_cost_56_65"]),
        (6, 7, params["arc_capacity_67_76"], params["unit_cost_67_76"]),
        (6, 9, params["arc_capacity_69_96"], params["unit_cost_69_96"]),
        (7, 8, params["arc_capacity_78_87"], params["unit_cost_78_87"]),
        (8, 9, params["arc_capacity_89_98"], params["unit_cost_89_98"]),
    ]
    demand_data = {
        1: params["demand_flow1_5_to_4"],
        2: params["demand_flow2_3_to_0"],
    }
    sources = {1: 5, 2: 3}
    destinations = {1: 4, 2: 0}

    nodes = list(range(10))
    commodities = [1, 2]
    arcs = []
    capacity_data = {}
    cost_data = {}
    outgoing = {node: [] for node in nodes}
    incoming = {node: [] for node in nodes}

    for first, second, capacity, cost in edge_data:
        for tail, head in ((first, second), (second, first)):
            arcs.append((tail, head))
            capacity_data[tail, head] = capacity
            cost_data[tail, head] = cost
            outgoing[tail].append(head)
            incoming[head].append(tail)

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.commodities = pyo.Set(initialize=commodities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )
    model.arc_unit_cost = pyo.Param(
        model.arcs,
        initialize=cost_data,
        within=pyo.Reals,
    )
    model.flow_demand = pyo.Param(
        model.commodities,
        initialize=demand_data,
        within=pyo.NonNegativeReals,
    )

    model.traffic = pyo.Var(
        model.commodities,
        model.arcs,
        domain=pyo.NonNegativeReals,
    )
    model.peak_utilization = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, 1),
    )

    def conservation_rule(network, commodity, node):
        net_outflow = (
            sum(
                network.traffic[commodity, node, head]
                for head in outgoing[node]
            )
            - sum(
                network.traffic[commodity, tail, node]
                for tail in incoming[node]
            )
        )
        if node == sources[commodity]:
            return net_outflow == network.flow_demand[commodity]
        if node == destinations[commodity]:
            return net_outflow == -network.flow_demand[commodity]
        return net_outflow == 0

    model.flow_conservation = pyo.Constraint(
        model.commodities,
        model.nodes,
        rule=conservation_rule,
    )

    def capacity_rule(network, tail, head):
        return (
            sum(
                network.traffic[commodity, tail, head]
                for commodity in network.commodities
            )
            <= network.arc_capacity[tail, head]
        )

    model.physical_capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def utilization_rule(network, tail, head):
        return (
            sum(
                network.traffic[commodity, tail, head]
                for commodity in network.commodities
            )
            <= (
                network.peak_utilization
                * network.arc_capacity[tail, head]
            )
        )

    model.peak_utilization_limits = pyo.Constraint(
        model.arcs,
        rule=utilization_rule,
    )

    model.routing_objective = pyo.Objective(
        expr=model.peak_utilization,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.routing_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
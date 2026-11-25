# IR: {"sets":{"N":"0..11","S":"1..11","D":"0..1","E":"{(i,j): i,j in N, i<j}","A":"{(i,j): i in N, j in S, i!=j}"},"params":{"coordinates[n,d]":"params['node_coordinates'][n][d]","cost[i,j]":"params['edge_costs'][i][j] for (i,j) in E; use upper triangle","B":"params['max_branch_size']"},"variables":{"x[i,j]":"binary for (i,j) in A","f[i,j]":"nonnegative real for (i,j) in A"},"constraints":{"one_parent[j]":"sum(i:(i,j) in A) x[i,j] = 1 for j in S","station_balance[j]":"sum(i:(i,j) in A) f[i,j] - sum(k:(j,k) in A) f[j,k] = 1 for j in S","root_supply":"sum(j in S) f[0,j] = |S|","flow_capacity[i,j]":"f[i,j] <= B*x[i,j] for (i,j) in A"},"objective":"minimize sum((i,j) in A) cost[min(i,j),max(i,j)]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Build and solve the capacitated rooted spanning-tree problem.

    Expected inputs:
        node_coordinates: 12 rows containing two coordinates each.
        edge_costs: a 12-by-12 matrix whose upper triangle contains costs.
        max_branch_size: maximum number of stations per root feeder subtree.

    Coordinates are retained as model data. Surveyed edge costs, rather
    than distances calculated from coordinates, determine the objective.
    """
    node_coordinates = params["node_coordinates"]
    edge_costs = params["edge_costs"]
    max_branch_size = params["max_branch_size"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 11)
    model.stations = pyo.RangeSet(1, 11)
    model.dimensions = pyo.RangeSet(0, 1)

    model.edges = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i < j
        ],
    )
    # Arcs into the transformer are excluded.
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.stations
            if i != j
        ],
    )

    model.coordinates = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize=lambda mdl, n, d: node_coordinates[n][d],
        within=pyo.Reals,
    )
    model.cable_cost = pyo.Param(
        model.edges,
        initialize=lambda mdl, i, j: edge_costs[i][j],
        within=pyo.Reals,
    )
    model.branch_limit = pyo.Param(
        initialize=max_branch_size,
        within=pyo.NonNegativeReals,
    )

    model.selected = pyo.Var(model.arcs, domain=pyo.Binary)
    model.station_flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def one_parent_rule(mdl, j):
        return sum(
            mdl.selected[i, j] for i in mdl.nodes if i != j
        ) == 1

    model.one_parent = pyo.Constraint(
        model.stations, rule=one_parent_rule
    )

    def station_balance_rule(mdl, j):
        incoming = sum(
            mdl.station_flow[i, j] for i in mdl.nodes if i != j
        )
        outgoing = sum(
            mdl.station_flow[j, k] for k in mdl.stations if k != j
        )
        return incoming - outgoing == 1

    model.station_balance = pyo.Constraint(
        model.stations, rule=station_balance_rule
    )

    model.root_supply = pyo.Constraint(
        expr=sum(
            model.station_flow[0, j] for j in model.stations
        ) == len(model.stations)
    )

    model.flow_capacity = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, i, j: (
            mdl.station_flow[i, j]
            <= mdl.branch_limit * mdl.selected[i, j]
        ),
    )

    # Parent constraints and positive station demand exclude disconnected
    # cycles, producing a rooted tree. Flow on each selected arc equals
    # its downstream station count, so root arcs enforce feeder capacity.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cable_cost[min(i, j), max(i, j)]
            * model.selected[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # Appsi can raise RuntimeError when no solution can be loaded.
    # Success is determined exclusively by objective retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
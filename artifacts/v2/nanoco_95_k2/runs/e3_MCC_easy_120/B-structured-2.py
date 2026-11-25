# IR: {"sets":{"U":"range(params['num_units'])","E":"range(params['num_pipelines'])","D":[0,1],"arcs":[[0,1],[0,3],[0,6],[1,0],[1,2],[1,3],[1,6],[2,1],[2,3],[3,2],[3,4],[4,2],[4,3],[4,5],[5,4],[5,6],[6,0],[6,5]]},"params":{"lower_bounds":"pipeline minimum flows, indexed by E","upper_bounds":"pipeline maximum flows, indexed by E","energy_costs":"pipeline costs, indexed by E","unit_coords":"spatial metadata indexed by U,D; does not affect costs or feasibility","num_units":"frozen unit count, 7","num_pipelines":"frozen pipeline count, 18"},"variables":{"flow[e]":"continuous nonnegative real, e in E"},"constraints":["lower_bounds[e] <= flow[e] <= upper_bounds[e] for each e in E","sum(flow[e] for e entering u) == sum(flow[e] for e leaving u) for each u in U"],"objective":"minimize sum(energy_costs[e] * flow[e] for e in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_units = params["num_units"]
    num_pipelines = params["num_pipelines"]
    lower_bounds = params["lower_bounds"]
    upper_bounds = params["upper_bounds"]
    energy_costs = params["energy_costs"]
    unit_coords = params["unit_coords"]

    arcs = (
        (0, 1),
        (0, 3),
        (0, 6),
        (1, 0),
        (1, 2),
        (1, 3),
        (1, 6),
        (2, 1),
        (2, 3),
        (3, 2),
        (3, 4),
        (4, 2),
        (4, 3),
        (4, 5),
        (5, 4),
        (5, 6),
        (6, 0),
        (6, 5),
    )

    if num_units != 7 or num_pipelines != len(arcs):
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()

    model.units = pyo.Set(initialize=range(num_units), ordered=True)
    model.pipelines = pyo.Set(initialize=range(num_pipelines), ordered=True)
    model.dimensions = pyo.Set(initialize=(0, 1), ordered=True)

    model.minimum_flow = pyo.Param(
        model.pipelines,
        initialize={edge: lower_bounds[edge] for edge in model.pipelines},
        within=pyo.Reals,
    )
    model.maximum_flow = pyo.Param(
        model.pipelines,
        initialize={edge: upper_bounds[edge] for edge in model.pipelines},
        within=pyo.Reals,
    )
    model.pumping_cost = pyo.Param(
        model.pipelines,
        initialize={edge: energy_costs[edge] for edge in model.pipelines},
        within=pyo.Reals,
    )
    model.coordinates = pyo.Param(
        model.units,
        model.dimensions,
        initialize={
            (unit, dimension): unit_coords[unit][dimension]
            for unit in model.units
            for dimension in model.dimensions
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.pipelines, domain=pyo.NonNegativeReals)

    def pipeline_limits_rule(network, edge):
        return (
            network.minimum_flow[edge],
            network.flow[edge],
            network.maximum_flow[edge],
        )

    model.pipeline_limits = pyo.Constraint(
        model.pipelines, rule=pipeline_limits_rule
    )

    incoming = {
        unit: tuple(
            edge
            for edge, (_, destination) in enumerate(arcs)
            if destination == unit
        )
        for unit in model.units
    }
    outgoing = {
        unit: tuple(
            edge
            for edge, (origin, _) in enumerate(arcs)
            if origin == unit
        )
        for unit in model.units
    }

    def mass_balance_rule(network, unit):
        return sum(network.flow[edge] for edge in incoming[unit]) == sum(
            network.flow[edge] for edge in outgoing[unit]
        )

    model.mass_balance = pyo.Constraint(model.units, rule=mass_balance_rule)

    model.total_energy = pyo.Objective(
        expr=sum(
            model.pumping_cost[edge] * model.flow[edge]
            for edge in model.pipelines
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_energy))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"units":"range(num_units), frozen size 7","pipelines":"range(num_pipelines), frozen size 18","axes":[0,1],"arcs":[[0,1],[0,3],[0,6],[1,0],[1,2],[1,3],[1,6],[2,1],[2,3],[3,2],[3,4],[4,2],[4,3],[4,5],[5,4],[5,6],[6,0],[6,5]]},"params":{"lower_bounds":"pipeline minimum flows","upper_bounds":"pipeline maximum flows","energy_costs":"pipeline costs per unit flow","unit_coords":"unit-by-axis spatial metadata; does not affect feasibility or cost","num_units":"frozen unit count","num_pipelines":"frozen pipeline count"},"variables":{"flow[p]":"continuous nonnegative"},"constraints":["flow[p] >= lower_bounds[p] for every pipeline p","flow[p] <= upper_bounds[p] for every pipeline p","sum(flow[p] for p entering u) == sum(flow[p] for p leaving u) for every unit u"],"objective":"minimize sum(energy_costs[p] * flow[p] for every pipeline p)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lower_bounds = params["lower_bounds"]
    upper_bounds = params["upper_bounds"]
    energy_costs = params["energy_costs"]
    unit_coords = params["unit_coords"]
    num_units = params["num_units"]
    num_pipelines = params["num_pipelines"]

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
        raise ValueError("The network structure requires 7 units and 18 pipelines.")

    for parameter_name, values in (
        ("lower_bounds", lower_bounds),
        ("upper_bounds", upper_bounds),
        ("energy_costs", energy_costs),
    ):
        if len(values) != num_pipelines:
            raise ValueError(
                f"{parameter_name} must have one entry per pipeline."
            )

    if len(unit_coords) != num_units:
        raise ValueError("unit_coords must have one entry per unit.")
    if any(len(unit_coords[unit]) != 2 for unit in range(num_units)):
        raise ValueError("Each unit must have exactly two coordinates.")

    incoming = {
        unit: tuple(
            pipeline
            for pipeline, (_, destination) in enumerate(arcs)
            if destination == unit
        )
        for unit in range(num_units)
    }
    outgoing = {
        unit: tuple(
            pipeline
            for pipeline, (origin, _) in enumerate(arcs)
            if origin == unit
        )
        for unit in range(num_units)
    }

    model = pyo.ConcreteModel()
    model.units = pyo.Set(initialize=range(num_units), ordered=True)
    model.pipelines = pyo.Set(initialize=range(num_pipelines), ordered=True)
    model.axes = pyo.Set(initialize=(0, 1), ordered=True)

    model.minimum_flow = pyo.Param(
        model.pipelines,
        initialize=lambda mdl, pipeline: lower_bounds[pipeline],
        within=pyo.Reals,
    )
    model.maximum_flow = pyo.Param(
        model.pipelines,
        initialize=lambda mdl, pipeline: upper_bounds[pipeline],
        within=pyo.Reals,
    )
    model.energy_cost = pyo.Param(
        model.pipelines,
        initialize=lambda mdl, pipeline: energy_costs[pipeline],
        within=pyo.Reals,
    )
    model.coordinates = pyo.Param(
        model.units,
        model.axes,
        initialize=lambda mdl, unit, axis: unit_coords[unit][axis],
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.pipelines, domain=pyo.NonNegativeReals)

    model.minimum_flow_constraints = pyo.Constraint(
        model.pipelines,
        rule=lambda mdl, pipeline: (
            mdl.flow[pipeline] >= mdl.minimum_flow[pipeline]
        ),
    )
    model.maximum_flow_constraints = pyo.Constraint(
        model.pipelines,
        rule=lambda mdl, pipeline: (
            mdl.flow[pipeline] <= mdl.maximum_flow[pipeline]
        ),
    )

    def mass_balance_rule(mdl, unit):
        return (
            sum(mdl.flow[pipeline] for pipeline in incoming[unit])
            == sum(mdl.flow[pipeline] for pipeline in outgoing[unit])
        )

    model.mass_balance = pyo.Constraint(
        model.units, rule=mass_balance_rule
    )
    model.total_energy = pyo.Objective(
        expr=sum(
            model.energy_cost[pipeline] * model.flow[pipeline]
            for pipeline in model.pipelines
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading finds no solution.
        # Continue to the objective-retrieval test; propagate unexpected errors.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_energy))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
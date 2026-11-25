# IR: {"sets":{"devices":[0,1,2,3,4,5,6,7],"edges":[[0,1],[2,4],[2,7],[3,7],[1,4],[2,3],[0,5],[2,5],[3,5]]},"params":{"durations":"params['durations'][i] for each device i","H":"sum(durations[i] for i in devices)"},"variables":{"start[i]":"continuous >= 0","closing_time":"continuous in [0,H]","before[i,j]":"binary for each edge (i,j)"},"constraints":["closing_time >= start[i] + durations[i] for each device i","start[i] + durations[i] <= start[j] + H*(1-before[i,j]) for each edge (i,j)","start[j] + durations[j] <= start[i] + H*before[i,j] for each edge (i,j)"],"objective":"minimize closing_time"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    devices = tuple(range(8))
    edges = (
        (0, 1),
        (2, 4),
        (2, 7),
        (3, 7),
        (1, 4),
        (2, 3),
        (0, 5),
        (2, 5),
        (3, 5),
    )

    duration_data = params["durations"]

    model = pyo.ConcreteModel()
    model.devices = pyo.Set(initialize=devices, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)

    model.duration = pyo.Param(
        model.devices,
        initialize={device: duration_data[device] for device in devices},
        within=pyo.NonNegativeReals,
    )
    model.horizon_bound = pyo.Param(
        initialize=sum(
            pyo.value(model.duration[device]) for device in devices
        ),
        within=pyo.NonNegativeReals,
    )

    model.start = pyo.Var(model.devices, domain=pyo.NonNegativeReals)
    model.closing_time = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, pyo.value(model.horizon_bound)),
    )
    model.before = pyo.Var(model.edges, domain=pyo.Binary)

    def completion_rule(instance, device):
        return (
            instance.closing_time
            >= instance.start[device] + instance.duration[device]
        )

    model.completion_constraints = pyo.Constraint(
        model.devices, rule=completion_rule
    )

    def forward_rule(instance, first, second):
        return (
            instance.start[first] + instance.duration[first]
            <= instance.start[second]
            + instance.horizon_bound * (1 - instance.before[first, second])
        )

    model.forward_constraints = pyo.Constraint(
        model.edges, rule=forward_rule
    )

    def reverse_rule(instance, first, second):
        return (
            instance.start[second] + instance.duration[second]
            <= instance.start[first]
            + instance.horizon_bound * instance.before[first, second]
        )

    model.reverse_constraints = pyo.Constraint(
        model.edges, rule=reverse_rule
    )

    model.total_horizon = pyo.Objective(
        expr=model.closing_time,
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        failure_reason = "no_feasible_solution"

    try:
        obj_val = float(pyo.value(model.total_horizon))
    except ValueError:
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}
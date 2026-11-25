# IR: {"sets":{"devices":"0..7","edges":[[0,1],[2,4],[2,7],[3,7],[1,4],[2,3],[0,5],[2,5],[3,5]]},"params":{"durations":"params['durations'][i] for each device i","H":"sum(durations[i] for i in devices)"},"variables":{"start[i]":"continuous, 0 <= start[i] <= H-durations[i]","order[i,j]":"binary for each edge (i,j)","horizon":"continuous, 0 <= horizon <= H"},"constraints":["start[i]+durations[i] <= horizon for each device i","start[i]+durations[i] <= start[j]+H*(1-order[i,j]) for each edge (i,j)","start[j]+durations[j] <= start[i]+H*order[i,j] for each edge (i,j)"],"intervals":"Device i occupies [start[i], start[i]+durations[i]); adjacent intervals may share an endpoint.","objective":"minimize horizon"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    devices = range(8)
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

    durations = {
        device: float(params["durations"][device])
        for device in devices
    }
    upper_horizon = sum(durations.values())

    model = pyo.ConcreteModel()
    model.devices = pyo.Set(initialize=devices, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)

    model.start = pyo.Var(
        model.devices,
        domain=pyo.NonNegativeReals,
        bounds=lambda instance, device: (
            0,
            upper_horizon - durations[device],
        ),
    )
    model.order = pyo.Var(model.edges, domain=pyo.Binary)
    model.horizon = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, upper_horizon),
    )

    def closing_time_rule(instance, device):
        return (
            instance.start[device] + durations[device]
            <= instance.horizon
        )

    model.closing_time = pyo.Constraint(
        model.devices,
        rule=closing_time_rule,
    )

    def forward_separation_rule(instance, first, second):
        return (
            instance.start[first] + durations[first]
            <= instance.start[second]
            + upper_horizon * (1 - instance.order[first, second])
        )

    model.forward_separation = pyo.Constraint(
        model.edges,
        rule=forward_separation_rule,
    )

    def reverse_separation_rule(instance, first, second):
        return (
            instance.start[second] + durations[second]
            <= instance.start[first]
            + upper_horizon * instance.order[first, second]
        )

    model.reverse_separation = pyo.Constraint(
        model.edges,
        rule=reverse_separation_rule,
    )

    model.schedule_objective = pyo.Objective(
        expr=model.horizon,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.schedule_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
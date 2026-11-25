# IR: {"sets":{"D":"{0,...,7}","E":"tuple-normalized params['interference_edges'] (frozen)"},"params":{"d[i]":"params['durations'][i]","H":"sum(d[i] for i in D)"},"variables":{"s[i]":"continuous, 0 <= s[i] <= H","C":"continuous, 0 <= C <= H","y[i,j]":"binary for (i,j) in E"},"constraints":["s[i] + d[i] <= C for i in D","s[i] + d[i] <= s[j] + H*(1-y[i,j]) for (i,j) in E","s[j] + d[j] <= s[i] + H*y[i,j] for (i,j) in E"],"objective":"minimize C"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.devices = pyo.RangeSet(0, 7)
    model.interference = pyo.Set(
        dimen=2,
        within=model.devices * model.devices,
        initialize=[tuple(edge) for edge in params["interference_edges"]],
    )

    model.duration = pyo.Param(
        model.devices,
        initialize={
            device: params["durations"][device]
            for device in model.devices
        },
        within=pyo.NonNegativeReals,
    )
    model.horizon_bound = pyo.Param(
        initialize=sum(
            params["durations"][device]
            for device in model.devices
        ),
        within=pyo.NonNegativeReals,
    )

    model.start_time = pyo.Var(
        model.devices,
        domain=pyo.NonNegativeReals,
        bounds=lambda mdl, device: (0, mdl.horizon_bound),
    )
    model.closing_time = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, model.horizon_bound),
    )
    model.precedes = pyo.Var(
        model.interference,
        domain=pyo.Binary,
    )

    def completion_rule(mdl, device):
        return (
            mdl.start_time[device] + mdl.duration[device]
            <= mdl.closing_time
        )

    model.completion_limits = pyo.Constraint(
        model.devices,
        rule=completion_rule,
    )

    def forward_rule(mdl, first, second):
        return (
            mdl.start_time[first] + mdl.duration[first]
            <= mdl.start_time[second]
            + mdl.horizon_bound * (1 - mdl.precedes[first, second])
        )

    model.forward_separation = pyo.Constraint(
        model.interference,
        rule=forward_rule,
    )

    def reverse_rule(mdl, first, second):
        return (
            mdl.start_time[second] + mdl.duration[second]
            <= mdl.start_time[first]
            + mdl.horizon_bound * mdl.precedes[first, second]
        )

    model.reverse_separation = pyo.Constraint(
        model.interference,
        rule=reverse_rule,
    )

    model.total_horizon = pyo.Objective(
        expr=model.closing_time,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_horizon))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
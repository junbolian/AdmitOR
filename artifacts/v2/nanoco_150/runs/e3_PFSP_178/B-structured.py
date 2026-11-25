# IR: {"sets":{"lots":[0,1,2,3],"positions":[0,1,2,3],"layers":[0,1,2]},"params":{"p[0,l]":"params['processing_time_W0'][l]","p[1,l]":"params['processing_time_W1'][l]","p[2,l]":"params['processing_time_W2'][l]","p[3,l]":"params['processing_time_W3'][l]"},"variables":{"x[w,k]":"binary; lot w occupies position k","C[k,l]":"nonnegative continuous; completion time at position k, layer l"},"expressions":{"d[k,l]":"sum(w in lots) p[w,l]*x[w,k]"},"constraints":["sum(k in positions) x[w,k] = 1 for each lot w","sum(w in lots) x[w,k] = 1 for each position k","C[k,l] >= d[k,l] for each position k and layer l","C[k,l] >= C[k-1,l] + d[k,l] for each k > 0 and layer l","C[k,l] >= C[k,l-1] + d[k,l] for each position k and l > 0"],"objective":"minimize C[3,2]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = {
        0: params["processing_time_W0"],
        1: params["processing_time_W1"],
        2: params["processing_time_W2"],
        3: params["processing_time_W3"],
    }

    model = pyo.ConcreteModel()

    model.lots = pyo.RangeSet(0, 3)
    model.positions = pyo.RangeSet(0, 3)
    model.layers = pyo.RangeSet(0, 2)

    model.processing_duration = pyo.Param(
        model.lots,
        model.layers,
        initialize=lambda mdl, wafer, layer: processing_times[wafer][layer],
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.lots, model.positions, domain=pyo.Binary
    )
    model.completion = pyo.Var(
        model.positions, model.layers, domain=pyo.NonNegativeReals
    )

    def assigned_duration_rule(mdl, position, layer):
        return sum(
            mdl.processing_duration[wafer, layer]
            * mdl.assignment[wafer, position]
            for wafer in mdl.lots
        )

    model.assigned_duration = pyo.Expression(
        model.positions, model.layers, rule=assigned_duration_rule
    )

    def lot_assignment_rule(mdl, wafer):
        return sum(
            mdl.assignment[wafer, position]
            for position in mdl.positions
        ) == 1

    model.lot_assignment = pyo.Constraint(
        model.lots, rule=lot_assignment_rule
    )

    def position_assignment_rule(mdl, position):
        return sum(
            mdl.assignment[wafer, position]
            for wafer in mdl.lots
        ) == 1

    model.position_assignment = pyo.Constraint(
        model.positions, rule=position_assignment_rule
    )

    def nonnegative_start_rule(mdl, position, layer):
        return (
            mdl.completion[position, layer]
            >= mdl.assigned_duration[position, layer]
        )

    model.nonnegative_start = pyo.Constraint(
        model.positions, model.layers, rule=nonnegative_start_rule
    )

    def station_sequence_rule(mdl, position, layer):
        if position == 0:
            return pyo.Constraint.Skip
        return (
            mdl.completion[position, layer]
            >= mdl.completion[position - 1, layer]
            + mdl.assigned_duration[position, layer]
        )

    model.station_sequence = pyo.Constraint(
        model.positions, model.layers, rule=station_sequence_rule
    )

    def layer_precedence_rule(mdl, position, layer):
        if layer == 0:
            return pyo.Constraint.Skip
        return (
            mdl.completion[position, layer]
            >= mdl.completion[position, layer - 1]
            + mdl.assigned_duration[position, layer]
        )

    model.layer_precedence = pyo.Constraint(
        model.positions, model.layers, rule=layer_precedence_rule
    )

    model.makespan_objective = pyo.Objective(
        expr=model.completion[3, 2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
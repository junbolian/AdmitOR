# IR: {"sets":{"lots":[0,1,2],"stations":[0,1,2],"pairs":[[0,1],[0,2],[1,2]]},"params":{"p[i,k]":"params[f'p_{i}_{k}']; nonnegative processing times","H":"sum(p[i,k] for all lots i and stations k)"},"variables":{"start[i,k]":"continuous, 0 <= start <= H","finish[i,k]":"continuous, 0 <= finish <= H","before[i,j,k]":"binary for i < j; 1 means i precedes j on station k","makespan":"continuous, 0 <= makespan <= H"},"constraints":["finish[i,k] = start[i,k] + p[i,k]","start[i,k+1] >= finish[i,k] for k in {0,1}","start[j,k] >= finish[i,k] - H*(1-before[i,j,k]) for i < j","start[i,k] >= finish[j,k] - H*before[i,j,k] for i < j","makespan >= finish[i,2] for each lot i"],"objective":"minimize makespan"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lots = range(3)
    stations = range(3)
    pairs = [(first, second) for first in lots for second in lots if first < second]

    processing = {
        (lot, station): params[f"p_{lot}_{station}"]
        for lot in lots
        for station in stations
    }

    model = pyo.ConcreteModel()
    model.lots = pyo.Set(initialize=lots, ordered=True)
    model.stations = pyo.Set(initialize=stations, ordered=True)
    model.pairs = pyo.Set(dimen=2, initialize=pairs, ordered=True)
    model.route_links = pyo.Set(initialize=[0, 1], ordered=True)

    model.processing = pyo.Param(
        model.lots,
        model.stations,
        initialize=processing,
        within=pyo.NonNegativeReals,
    )
    horizon = sum(
        pyo.value(model.processing[lot, station])
        for lot in model.lots
        for station in model.stations
    )
    model.horizon = pyo.Param(initialize=horizon, within=pyo.NonNegativeReals)

    model.start = pyo.Var(
        model.lots,
        model.stations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.finish = pyo.Var(
        model.lots,
        model.stations,
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )
    model.before = pyo.Var(
        model.pairs,
        model.stations,
        domain=pyo.Binary,
    )
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def processing_rule(instance, lot, station):
        return (
            instance.finish[lot, station]
            == instance.start[lot, station] + instance.processing[lot, station]
        )

    model.processing_constraints = pyo.Constraint(
        model.lots, model.stations, rule=processing_rule
    )

    # Transfers have no modeled duration. Processing follows the stated
    # completion-before-start precedence; waiting for a station is permitted.
    def route_rule(instance, lot, station):
        return instance.start[lot, station + 1] >= instance.finish[lot, station]

    model.route_constraints = pyo.Constraint(
        model.lots, model.route_links, rule=route_rule
    )

    def first_before_second_rule(instance, first, second, station):
        return instance.start[second, station] >= (
            instance.finish[first, station]
            - instance.horizon * (1 - instance.before[first, second, station])
        )

    model.first_before_second_constraints = pyo.Constraint(
        model.pairs, model.stations, rule=first_before_second_rule
    )

    def second_before_first_rule(instance, first, second, station):
        return instance.start[first, station] >= (
            instance.finish[second, station]
            - instance.horizon * instance.before[first, second, station]
        )

    model.second_before_first_constraints = pyo.Constraint(
        model.pairs, model.stations, rule=second_before_first_rule
    )

    def makespan_rule(instance, lot):
        return instance.makespan >= instance.finish[lot, 2]

    model.makespan_constraints = pyo.Constraint(
        model.lots, rule=makespan_rule
    )
    model.total_cycle_time = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver errors propagate to the calling harness.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cycle_time))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"L":"L_0..L_9","S":"0..7","A":"all ordered pairs of distinct stations","K":["OD_6_7","OD_6_1","OD_3_0","OD_4_6","OD_1_0","OD_5_3","OD_4_2","OD_4_1","OD_1_4","OD_2_3","OD_4_0","OD_6_4"]},"params":{"fixed_cost":"L-indexed","operational_cost_per_freq":"L-indexed","capacity_per_trip":"L-indexed","resource_usage_per_trip":"L-indexed","min_frequency":"scalar","max_frequency":"scalar","demand":"K-indexed","penalty_unmet":"K-indexed","total_resource_budget":"scalar"},"assumptions":["No physical network is supplied: all directed station arcs are eligible, and each selected line forms a simple directed path.","A line may serve an OD only if it visits the origin before the destination.","Capacity is aggregated independently for each OD, as stated.","The OD minimum-frequency constraint is unconditional, as stated."],"variables":{"selected[L]":"binary","frequency[L]":"nonnegative continuous","unmet[K]":"nonnegative continuous","arc_used[L,A]":"binary","visited[L,S]":"binary","route_start[L,S]":"binary","route_end[L,S]":"binary","position[L,S]":"continuous in [0,|S|-1]","serves[L,K]":"binary","od_frequency[L,K]":"nonnegative continuous","transfer[S]":"binary"},"constraints":["min_frequency*selected[l] <= frequency[l] <= max_frequency*selected[l]","sum_l resource_usage_per_trip[l]*frequency[l] <= total_resource_budget","sum_s route_start[l,s] = selected[l]; sum_s route_end[l,s] = selected[l]","sum_j arc_used[l,s,j] = visited[l,s]-route_end[l,s]","sum_i arc_used[l,i,s] = visited[l,s]-route_start[l,s]","visited[l,s] <= selected[l]","route_start[l,s]+route_end[l,s] <= visited[l,s]","position[l,j] >= position[l,i]+1-|S|*(1-arc_used[l,i,j])","serves[l,k] <= visited[l,origin[k]]; serves[l,k] <= visited[l,destination[k]]","position[l,destination[k]] >= position[l,origin[k]]+1-|S|*(1-serves[l,k])","od_frequency[l,k] <= frequency[l]","od_frequency[l,k] <= max_frequency*serves[l,k]","od_frequency[l,k] >= frequency[l]-max_frequency*(1-serves[l,k])","sum_l capacity_per_trip[l]*od_frequency[l,k]+unmet[k] >= demand[k]","sum_l od_frequency[l,k] >= min_frequency","2*transfer[s] <= sum_l visited[l,s]"],"objective":"minimize sum_l(fixed_cost[l]*selected[l]+operational_cost_per_freq[l]*frequency[l])+sum_k penalty_unmet[k]*unmet[k]"}
#
# The stated numerical instance is infeasible: operating any selected line
# requires at least 2*33 resource units, exceeding the budget of 50, whereas
# the unconditional OD frequency requirements prohibit selecting no lines.
# Unmet-demand variables do not relax those frequency requirements. This
# implementation preserves the stated constraints rather than silently
# changing them to force a feasible result.

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lines = tuple(f"L_{idx}" for idx in range(10))
    stations = tuple(range(8))
    endpoints = {
        "OD_6_7": (6, 7),
        "OD_6_1": (6, 1),
        "OD_3_0": (3, 0),
        "OD_4_6": (4, 6),
        "OD_1_0": (1, 0),
        "OD_5_3": (5, 3),
        "OD_4_2": (4, 2),
        "OD_4_1": (4, 1),
        "OD_1_4": (1, 4),
        "OD_2_3": (2, 3),
        "OD_4_0": (4, 0),
        "OD_6_4": (6, 4),
    }
    od_pairs = tuple(endpoints)
    arcs = tuple(
        (origin, destination)
        for origin in stations
        for destination in stations
        if origin != destination
    )

    def indexed_values(raw, labels):
        if not isinstance(raw, Mapping):
            return {label: raw[idx] for idx, label in enumerate(labels)}
        values = {}
        for idx, label in enumerate(labels):
            if label in raw:
                values[label] = raw[label]
            elif idx in raw:
                values[label] = raw[idx]
            else:
                values[label] = raw[str(idx)]
        return values

    model = pyo.ConcreteModel()
    model.L = pyo.Set(initialize=lines, ordered=True)
    model.S = pyo.Set(initialize=stations, ordered=True)
    model.K = pyo.Set(initialize=od_pairs, ordered=True)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.fixed_cost = pyo.Param(
        model.L, initialize=indexed_values(params["fixed_cost"], lines)
    )
    model.operational_cost_per_freq = pyo.Param(
        model.L,
        initialize=indexed_values(params["operational_cost_per_freq"], lines),
    )
    model.capacity_per_trip = pyo.Param(
        model.L, initialize=indexed_values(params["capacity_per_trip"], lines)
    )
    model.resource_usage_per_trip = pyo.Param(
        model.L, initialize=indexed_values(params["resource_usage_per_trip"], lines)
    )
    model.min_frequency = pyo.Param(initialize=params["min_frequency"])
    model.max_frequency = pyo.Param(initialize=params["max_frequency"])
    model.demand = pyo.Param(
        model.K, initialize=indexed_values(params["demand"], od_pairs)
    )
    model.penalty_unmet = pyo.Param(
        model.K, initialize=indexed_values(params["penalty_unmet"], od_pairs)
    )
    model.total_resource_budget = pyo.Param(
        initialize=params["total_resource_budget"]
    )

    model.selected = pyo.Var(model.L, domain=pyo.Binary)
    model.frequency = pyo.Var(model.L, domain=pyo.NonNegativeReals)
    model.unmet = pyo.Var(model.K, domain=pyo.NonNegativeReals)
    model.arc_used = pyo.Var(model.L, model.A, domain=pyo.Binary)
    model.visited = pyo.Var(model.L, model.S, domain=pyo.Binary)
    model.route_start = pyo.Var(model.L, model.S, domain=pyo.Binary)
    model.route_end = pyo.Var(model.L, model.S, domain=pyo.Binary)
    model.position = pyo.Var(
        model.L, model.S, bounds=(0, len(stations) - 1)
    )
    model.serves = pyo.Var(model.L, model.K, domain=pyo.Binary)
    model.od_frequency = pyo.Var(
        model.L, model.K, domain=pyo.NonNegativeReals
    )
    model.transfer = pyo.Var(model.S, domain=pyo.Binary)

    model.requirements = pyo.ConstraintList()

    for line in lines:
        model.requirements.add(
            model.frequency[line] >= model.min_frequency * model.selected[line]
        )
        model.requirements.add(
            model.frequency[line] <= model.max_frequency * model.selected[line]
        )
        model.requirements.add(
            sum(model.route_start[line, station] for station in stations)
            == model.selected[line]
        )
        model.requirements.add(
            sum(model.route_end[line, station] for station in stations)
            == model.selected[line]
        )

        for station in stations:
            model.requirements.add(
                sum(
                    model.arc_used[line, station, destination]
                    for destination in stations
                    if destination != station
                )
                == model.visited[line, station] - model.route_end[line, station]
            )
            model.requirements.add(
                sum(
                    model.arc_used[line, origin, station]
                    for origin in stations
                    if origin != station
                )
                == model.visited[line, station] - model.route_start[line, station]
            )
            model.requirements.add(
                model.visited[line, station] <= model.selected[line]
            )
            model.requirements.add(
                model.route_start[line, station] + model.route_end[line, station]
                <= model.visited[line, station]
            )

        for origin, destination in arcs:
            model.requirements.add(
                model.position[line, destination]
                >= model.position[line, origin] + 1
                - len(stations) * (1 - model.arc_used[line, origin, destination])
            )

        for od in od_pairs:
            origin, destination = endpoints[od]
            model.requirements.add(
                model.serves[line, od] <= model.visited[line, origin]
            )
            model.requirements.add(
                model.serves[line, od] <= model.visited[line, destination]
            )
            model.requirements.add(
                model.position[line, destination]
                >= model.position[line, origin] + 1
                - len(stations) * (1 - model.serves[line, od])
            )
            model.requirements.add(
                model.od_frequency[line, od] <= model.frequency[line]
            )
            model.requirements.add(
                model.od_frequency[line, od]
                <= model.max_frequency * model.serves[line, od]
            )
            model.requirements.add(
                model.od_frequency[line, od]
                >= model.frequency[line]
                - model.max_frequency * (1 - model.serves[line, od])
            )

    model.requirements.add(
        sum(
            model.resource_usage_per_trip[line] * model.frequency[line]
            for line in lines
        )
        <= model.total_resource_budget
    )

    for od in od_pairs:
        model.requirements.add(
            sum(
                model.capacity_per_trip[line] * model.od_frequency[line, od]
                for line in lines
            )
            + model.unmet[od]
            >= model.demand[od]
        )
        model.requirements.add(
            sum(model.od_frequency[line, od] for line in lines)
            >= model.min_frequency
        )

    for station in stations:
        model.requirements.add(
            2 * model.transfer[station]
            <= sum(model.visited[line, station] for line in lines)
        )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[line] * model.selected[line]
            + model.operational_cost_per_freq[line] * model.frequency[line]
            for line in lines
        )
        + sum(model.penalty_unmet[od] * model.unmet[od] for od in od_pairs),
        sense=pyo.minimize,
    )

    # APPsi may raise when it cannot load a feasible solution. Still determine
    # success exclusively by attempting to retrieve the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"T":"fixed supplied roster, checked against params[num_driving_tasks]","P":"platforms, checked against params[num_platforms]","H":["A","M","Z"],"E":"chronological, colocated task connections satisfying the transfer buffer and necessary two-task mileage/shift bounds"},"params":{"mileage_A_M":"params[mileage_A_M]","mileage_Z_M":"params[mileage_Z_M]","max_continuous_driving_minutes":"params[max_continuous_driving_minutes]","max_daily_mileage_km":"params[max_daily_mileage_km]","min_transfer_buffer_minutes":"params[min_transfer_buffer_minutes]","max_shift_length_minutes":"params[max_shift_length_minutes]","num_driving_tasks":"params[num_driving_tasks], frozen","num_platforms":"params[num_platforms], frozen","derived":"task times, durations, mileage, adjacency, longest-path resource bounds, matching lower bound and feasible-cover upper bound"},"assumptions":["The example is the fixed 200-task roster on 40 platforms.","Duties may start and finish at A, M or Z; return to the starting platform is not required.","Every connection includes a qualifying break/handover that resets continuous driving; its minimum duration is the supplied transfer buffer.","Tasks cannot be split, and deadheading is unavailable."],"preprocessing":["Reject invalid parameters, cardinality mismatches and individually infeasible tasks.","Use maximum bipartite matching to obtain a valid driver-count lower bound.","Construct and check candidate task covers; fix a cover only when it is feasible and attains the matching lower bound.","Omit mileage or elapsed-duty resource variables only when DAG longest-path bounds prove that resource redundant."],"variables":{"x[i,j]":"binary selected connection for (i,j) in E","s[i]":"binary duty start","q[i]":"continuous cumulative mileage, present only if mileage is not redundant","w[i]":"continuous elapsed duty time through task i, present only if shift length is not redundant"},"constraints":["For every i: s[i]+sum_(j,i) x[j,i]=1.","For every i: sum_(i,j) x[i,j]<=1.","Duty starts and finishes must occur in H; satisfied structurally for this roster.","Continuous driving is bounded by the per-task feasibility check under the stated reset assumption.","matching_lower_bound<=sum_i s[i]<=feasible_cover_upper_bound.","If q exists: mileage[i]<=q[i]<=min(mileage_limit,longest_path_mileage[i]).","If q exists: q[i]<=mileage[i]+(q_upper[i]-mileage[i])*(1-s[i]).","If q exists, for every (i,j): q[j]>=q[i]+mileage[j]-q_upper[i]*(1-x[i,j]).","If w exists: duration[i]<=w[i]<=min(shift_limit,longest_path_elapsed[i]).","If w exists: w[i]<=duration[i]+(w_upper[i]-duration[i])*(1-s[i]).","If w exists, for every (i,j): w[j]>=w[i]+end[j]-end[i]-(w_upper[i]+start[j]-end[i])*(1-x[i,j]).","If a checked feasible cover attains the matching lower bound, fix x and s to that certified optimal cover."],"objective":"Minimize sum_i s[i], the number of driver duties."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    mileage_a_m = float(params["mileage_A_M"])
    mileage_z_m = float(params["mileage_Z_M"])
    continuous_limit = float(params["max_continuous_driving_minutes"])
    mileage_limit = float(params["max_daily_mileage_km"])
    transfer_buffer = float(params["min_transfer_buffer_minutes"])
    shift_limit = float(params["max_shift_length_minutes"])
    task_count_value = float(params["num_driving_tasks"])
    platform_count_value = float(params["num_platforms"])

    numeric_values = (
        mileage_a_m,
        mileage_z_m,
        continuous_limit,
        mileage_limit,
        transfer_buffer,
        shift_limit,
        task_count_value,
        platform_count_value,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        return {"objective": None, "status": "invalid_parameters"}

    if (
        min(numeric_values[:6]) < 0
        or not task_count_value.is_integer()
        or not platform_count_value.is_integer()
    ):
        return {"objective": None, "status": "invalid_parameters"}

    task_count = int(task_count_value)
    platform_count = int(platform_count_value)

    # Structural constants below encode the supplied example roster.
    if task_count != 200 or platform_count != 40:
        return {"objective": None, "status": "cardinality_mismatch"}

    # Work in seconds for exact roster timestamps. Parameter limits remain
    # supplied in minutes and are converted here.
    continuous_seconds = continuous_limit * 60.0
    buffer_seconds = transfer_buffer * 60.0
    shift_seconds = shift_limit * 60.0

    patterns = (
        (10 * 3600 + 3 * 60 + 11, 10 * 3600 + 57 * 60 + 43, "M", "Z"),
        (10 * 3600 + 3 * 60 + 43, 10 * 3600 + 58 * 60 + 32, "Z", "M"),
        (10 * 3600 + 4 * 60 + 10, 10 * 3600 + 39 * 60 + 11, "A", "M"),
        (10 * 3600 + 4 * 60 + 32, 10 * 3600 + 40 * 60 + 10, "M", "A"),
    )
    roster = [
        (
            pickup_seconds + group * 6 * 60,
            dropoff_seconds + group * 6 * 60,
            pickup,
            dropoff,
        )
        for group in range(50)
        for pickup_seconds, dropoff_seconds, pickup, dropoff in patterns
    ]

    task_ids = list(range(task_count))
    transfer_platforms = ("A", "M", "Z")
    platforms = list(transfer_platforms) + [
        "OTHER_{}".format(position)
        for position in range(platform_count - len(transfer_platforms))
    ]

    start_time = {task: roster[task][0] for task in task_ids}
    end_time = {task: roster[task][1] for task in task_ids}
    pickup_location = {task: roster[task][2] for task in task_ids}
    dropoff_location = {task: roster[task][3] for task in task_ids}
    duration = {
        task: end_time[task] - start_time[task] for task in task_ids
    }
    mileage = {
        task: (
            mileage_a_m
            if "A" in (pickup_location[task], dropoff_location[task])
            else mileage_z_m
        )
        for task in task_ids
    }
    chronological_tasks = sorted(
        task_ids, key=lambda task: (start_time[task], task)
    )

    for task in task_ids:
        if (
            duration[task] > continuous_seconds
            or duration[task] > shift_seconds
            or mileage[task] > mileage_limit
        ):
            return {"objective": None, "status": "infeasible"}

    predecessors = {task: [] for task in task_ids}
    successors = {task: [] for task in task_ids}
    arcs = []

    for previous in chronological_tasks:
        for following in chronological_tasks:
            if (
                start_time[following] >= end_time[previous] + buffer_seconds
                and dropoff_location[previous] == pickup_location[following]
                and dropoff_location[previous] in transfer_platforms
                and mileage[previous] + mileage[following] <= mileage_limit
                and end_time[following] - start_time[previous] <= shift_seconds
            ):
                arcs.append((previous, following))
                successors[previous].append(following)
                predecessors[following].append(previous)

    def maximum_matching(adjacency, left_order):
        matched_right = {}

        def augment(previous, visited_right):
            for following in adjacency[previous]:
                if following in visited_right:
                    continue
                visited_right.add(following)
                incumbent = matched_right.get(following)
                if incumbent is None or augment(incumbent, visited_right):
                    matched_right[following] = previous
                    return True
            return False

        for previous in left_order:
            augment(previous, set())

        return {
            previous: following
            for following, previous in matched_right.items()
        }

    def chains_from_connections(connections):
        incoming_tasks = set(connections.values())
        chains = []
        for first in chronological_tasks:
            if first in incoming_tasks:
                continue
            chain = [first]
            while chain[-1] in connections:
                chain.append(connections[chain[-1]])
            chains.append(chain)
        return chains

    def feasible_chains(chains):
        return all(
            math.fsum(mileage[task] for task in chain) <= mileage_limit
            and end_time[chain[-1]] - start_time[chain[0]] <= shift_seconds
            for chain in chains
        )

    matching = maximum_matching(successors, chronological_tasks)
    matching_lower_bound = task_count - len(matching)
    matching_chains = chains_from_connections(matching)

    # Singleton duties provide an unconditional feasible upper bound.
    best_chains = [[task] for task in chronological_tasks]
    certified_connections = None

    if feasible_chains(matching_chains):
        best_chains = matching_chains
        certified_connections = matching
    else:
        # A deterministic greedy cover often supplies a useful upper bound,
        # or an optimality certificate when it meets the matching bound.
        greedy_chains = []
        greedy_mileage = []

        for task in chronological_tasks:
            eligible = [
                chain_position
                for chain_position, chain in enumerate(greedy_chains)
                if (
                    dropoff_location[chain[-1]] == pickup_location[task]
                    and start_time[task]
                    >= end_time[chain[-1]] + buffer_seconds
                    and greedy_mileage[chain_position] + mileage[task]
                    <= mileage_limit
                    and end_time[task] - start_time[chain[0]]
                    <= shift_seconds
                )
            ]

            if eligible:
                chosen = min(
                    eligible,
                    key=lambda position: (
                        greedy_mileage[position],
                        -end_time[greedy_chains[position][-1]],
                        position,
                    ),
                )
                greedy_chains[chosen].append(task)
                greedy_mileage[chosen] = math.fsum(
                    mileage[item] for item in greedy_chains[chosen]
                )
            else:
                greedy_chains.append([task])
                greedy_mileage.append(mileage[task])

        if feasible_chains(greedy_chains):
            best_chains = greedy_chains

        if len(best_chains) == matching_lower_bound:
            certified_connections = {
                previous: following
                for chain in best_chains
                for previous, following in zip(chain, chain[1:])
            }

    # Compute valid resource bounds on the acyclic connection graph.
    # When a limit exceeds every possible path's consumption, omitting its
    # resource variables preserves the complete feasible set.
    longest_mileage = {}
    earliest_ancestor_start = {}
    longest_elapsed = {}

    for task in chronological_tasks:
        longest_mileage[task] = mileage[task] + max(
            (longest_mileage[previous] for previous in predecessors[task]),
            default=0.0,
        )
        earliest_ancestor_start[task] = min(
            [start_time[task]]
            + [
                earliest_ancestor_start[previous]
                for previous in predecessors[task]
            ]
        )
        longest_elapsed[task] = (
            end_time[task] - earliest_ancestor_start[task]
        )

    mileage_redundant = max(longest_mileage.values()) <= mileage_limit
    shift_redundant = max(longest_elapsed.values()) <= shift_seconds

    mileage_upper = {
        task: min(mileage_limit, longest_mileage[task])
        for task in task_ids
    }
    elapsed_upper = {
        task: min(shift_seconds, longest_elapsed[task])
        for task in task_ids
    }

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=task_ids, ordered=True)
    model.P = pyo.Set(initialize=platforms, ordered=True)
    model.H = pyo.Set(initialize=transfer_platforms, within=model.P)
    model.E = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.x = pyo.Var(model.E, domain=pyo.Binary)
    model.s = pyo.Var(model.T, domain=pyo.Binary)

    def coverage_rule(mdl, task):
        return (
            mdl.s[task]
            + pyo.quicksum(
                mdl.x[previous, task]
                for previous in predecessors[task]
            )
            == 1
        )

    def successor_rule(mdl, task):
        if not successors[task]:
            return pyo.Constraint.Skip
        return (
            pyo.quicksum(
                mdl.x[task, following]
                for following in successors[task]
            )
            <= 1
        )

    model.task_coverage = pyo.Constraint(model.T, rule=coverage_rule)
    model.single_successor = pyo.Constraint(model.T, rule=successor_rule)

    duty_count = pyo.quicksum(model.s[task] for task in model.T)
    model.driver_lower_bound = pyo.Constraint(
        expr=duty_count >= matching_lower_bound
    )
    model.driver_upper_bound = pyo.Constraint(
        expr=duty_count <= len(best_chains)
    )

    if not mileage_redundant:
        model.q = pyo.Var(
            model.T,
            domain=pyo.NonNegativeReals,
            bounds=lambda mdl, task: (
                mileage[task], mileage_upper[task]
            ),
        )

        def mileage_reset_rule(mdl, task):
            return mdl.q[task] <= (
                mileage[task]
                + (mileage_upper[task] - mileage[task])
                * (1 - mdl.s[task])
            )

        def mileage_link_rule(mdl, previous, following):
            return mdl.q[following] >= (
                mdl.q[previous]
                + mileage[following]
                - mileage_upper[previous]
                * (1 - mdl.x[previous, following])
            )

        model.mileage_reset = pyo.Constraint(
            model.T, rule=mileage_reset_rule
        )
        model.mileage_links = pyo.Constraint(
            model.E, rule=mileage_link_rule
        )

    if not shift_redundant:
        model.w = pyo.Var(
            model.T,
            domain=pyo.NonNegativeReals,
            bounds=lambda mdl, task: (
                duration[task], elapsed_upper[task]
            ),
        )

        def elapsed_reset_rule(mdl, task):
            return mdl.w[task] <= (
                duration[task]
                + (elapsed_upper[task] - duration[task])
                * (1 - mdl.s[task])
            )

        def elapsed_link_rule(mdl, previous, following):
            big_m = (
                elapsed_upper[previous]
                + start_time[following]
                - end_time[previous]
            )
            return mdl.w[following] >= (
                mdl.w[previous]
                + end_time[following]
                - end_time[previous]
                - big_m * (1 - mdl.x[previous, following])
            )

        model.elapsed_reset = pyo.Constraint(
            model.T, rule=elapsed_reset_rule
        )
        model.elapsed_links = pyo.Constraint(
            model.E, rule=elapsed_link_rule
        )

    if certified_connections is not None:
        incoming_tasks = set(certified_connections.values())
        for previous, following in arcs:
            model.x[previous, following].fix(
                int(certified_connections.get(previous) == following)
            )
        for task in task_ids:
            model.s[task].fix(int(task not in incoming_tasks))

    model.driver_count = pyo.Objective(
        expr=duty_count,
        sense=pyo.minimize,
    )

    # Selected x arcs encode each optimal task chain; selected s variables
    # identify its first task. The required return contract exposes only
    # the objective and status.
    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.driver_count))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
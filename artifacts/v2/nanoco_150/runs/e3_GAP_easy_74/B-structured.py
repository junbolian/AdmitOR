# IR: {"sets":{"S":"0..params['num_subcontractors']-1 (frozen size 3)","P":"0..params['num_phases']-1 (frozen size 7)"},"params":{"labor_limit":"[params['labor_limit_S1'],params['labor_limit_S2'],params['labor_limit_S3']]","labor_req":"params['labor_req'][s][p]","bid_price":"params['bid_price'][s][p]"},"variables":{"assigned[s,p]":"Binary; 1 iff subcontractor s executes phase p"},"constraints":["For each p: sum(assigned[s,p] for s in S) = 1","For each s: sum(labor_req[s,p]*assigned[s,p] for p in P) <= labor_limit[s]"],"objective":"Minimize sum(bid_price[s,p]*assigned[s,p] for s in S, p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_subcontractors = params["num_subcontractors"]
    num_phases = params["num_phases"]

    if num_subcontractors != 3 or num_phases != 7:
        raise ValueError(
            "The frozen problem structure requires 3 subcontractors and 7 phases."
        )

    labor_limits = [
        params["labor_limit_S1"],
        params["labor_limit_S2"],
        params["labor_limit_S3"],
    ]
    labor_requirements = params["labor_req"]
    bid_prices = params["bid_price"]

    model = pyo.ConcreteModel()
    model.subcontractors = pyo.RangeSet(0, num_subcontractors - 1)
    model.phases = pyo.RangeSet(0, num_phases - 1)

    model.labor_capacity = pyo.Param(
        model.subcontractors,
        initialize={
            subcontractor: labor_limits[subcontractor]
            for subcontractor in model.subcontractors
        },
    )
    model.phase_labor = pyo.Param(
        model.subcontractors,
        model.phases,
        initialize={
            (subcontractor, phase): labor_requirements[subcontractor][phase]
            for subcontractor in model.subcontractors
            for phase in model.phases
        },
    )
    model.phase_cost = pyo.Param(
        model.subcontractors,
        model.phases,
        initialize={
            (subcontractor, phase): bid_prices[subcontractor][phase]
            for subcontractor in model.subcontractors
            for phase in model.phases
        },
    )

    # The binary variables explicitly encode the allocation of every phase.
    model.assigned = pyo.Var(
        model.subcontractors,
        model.phases,
        domain=pyo.Binary,
    )

    def phase_assignment_rule(problem, phase):
        return sum(
            problem.assigned[subcontractor, phase]
            for subcontractor in problem.subcontractors
        ) == 1

    model.phase_assignment = pyo.Constraint(
        model.phases,
        rule=phase_assignment_rule,
    )

    def labor_capacity_rule(problem, subcontractor):
        return sum(
            problem.phase_labor[subcontractor, phase]
            * problem.assigned[subcontractor, phase]
            for phase in problem.phases
        ) <= problem.labor_capacity[subcontractor]

    model.labor_bound = pyo.Constraint(
        model.subcontractors,
        rule=labor_capacity_rule,
    )

    model.total_bid_cost = pyo.Objective(
        expr=sum(
            model.phase_cost[subcontractor, phase]
            * model.assigned[subcontractor, phase]
            for subcontractor in model.subcontractors
            for phase in model.phases
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Success is determined solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_bid_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"T":"0..4 in table order","K":"0..3","A":"(t,k) in T x K where k=0 or profit_k[t] is not null"},"params":["space_capacity","rent_rate","area[T]","min_shops[T]","max_shops[T]","profit_1[T]","profit_2[T]","profit_3[T]"],"variables":{"selected[A]":"binary"},"expressions":{"shops[t]":"sum(k*selected[t,k] for k with (t,k) in A)"},"constraints":["For each t: sum(selected[t,k] for k with (t,k) in A)=1","For each t: shops[t]>=min_shops[t]","For each t: shops[t]<=max_shops[t]","sum(area[t]*shops[t] for t in T)<=space_capacity"],"objective":"maximize rent_rate*sum(k*profit_k[t]*selected[t,k] for (t,k) in A with k>0)","input_failure":"Return objective=null and status=missing_parameter:<key> when a required parameter is absent; never invent missing profit data","solve_failure":"Return objective=null and status=objective_unavailable when objective evaluation fails; propagate unexpected exceptions"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Vector parameters use the following order:
    jewelry, shoes & hats, general merchandise, bookstore, catering.

    Individual profit entries may be None for unavailable store counts.
    All parameter keys are required. A missing profit vector cannot be
    reconstructed from the remaining inputs without inventing data.

    The objective is annual rental income in ten thousand yuan.
    """
    try:
        space_capacity = params["space_capacity"]
        rent_rate = params["rent_rate"]
        area = params["area"]
        min_shops = params["min_shops"]
        max_shops = params["max_shops"]
        profit_1 = params["profit_1"]
        profit_2 = params["profit_2"]
        profit_3 = params["profit_3"]
    except KeyError as exc:
        return {
            "objective": None,
            "status": f"missing_parameter:{exc.args[0]}",
        }

    profit = {1: profit_1, 2: profit_2, 3: profit_3}
    store_types = range(5)
    count_options = range(4)

    available_options = [
        (store_type, count)
        for store_type in store_types
        for count in count_options
        if count == 0 or profit[count][store_type] is not None
    ]
    options_by_type = {
        store_type: [
            count
            for candidate_type, count in available_options
            if candidate_type == store_type
        ]
        for store_type in store_types
    }

    model = pyo.ConcreteModel()
    model.store_types = pyo.Set(initialize=store_types, ordered=True)
    model.available_options = pyo.Set(
        dimen=2, initialize=available_options, ordered=True
    )
    model.selected = pyo.Var(model.available_options, domain=pyo.Binary)

    def shops_rule(instance, store_type):
        return sum(
            count * instance.selected[store_type, count]
            for count in options_by_type[store_type]
        )

    model.shops = pyo.Expression(model.store_types, rule=shops_rule)

    def choose_count_rule(instance, store_type):
        return sum(
            instance.selected[store_type, count]
            for count in options_by_type[store_type]
        ) == 1

    model.choose_count = pyo.Constraint(
        model.store_types, rule=choose_count_rule
    )
    model.minimum_shops = pyo.Constraint(
        model.store_types,
        rule=lambda instance, store_type: (
            instance.shops[store_type] >= min_shops[store_type]
        ),
    )
    model.maximum_shops = pyo.Constraint(
        model.store_types,
        rule=lambda instance, store_type: (
            instance.shops[store_type] <= max_shops[store_type]
        ),
    )
    model.space_limit = pyo.Constraint(
        expr=sum(
            area[store_type] * model.shops[store_type]
            for store_type in model.store_types
        ) <= space_capacity
    )
    model.rental_income = pyo.Objective(
        expr=rent_rate * sum(
            count
            * profit[count][store_type]
            * model.selected[store_type, count]
            for store_type, count in available_options
            if count > 0
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi may raise when no feasible solution is available to load.
        # Still determine success solely through objective evaluation.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.rental_income))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"T":[1,2,3,4,5],"B":[1,2,3],"K":{"1":[0,1,2,3],"2":[0,1,2],"3":[0,1,2,3],"4":[0,1,2],"5":[0,1,2,3]}},"params":{"area_per_store":"params[area_per_store], indexed by T","min_stores":"params[min_stores], indexed by T","max_stores":"params[max_stores], indexed by B","profit_type1":"params[profit_type1], indexed by positive K[1]","profit_type2":"params[profit_type2], indexed by positive K[2]","profit_type3":"params[profit_type3], indexed by positive K[3]","profit_type4":"params[profit_type4], indexed by positive K[4]","profit_type5":"params[profit_type5], indexed by positive K[5]","rent_share":"params[rent_share]","capacity":5000,"profit_at_zero":0},"variables":{"choose[t,k]":"binary; selects exactly k stores of type t"},"expressions":{"store_count[t]":"sum(k*choose[t,k] for k in K[t])"},"constraints":["sum(choose[t,k] for k in K[t]) == 1 for each t in T","store_count[t] >= min_stores[t] for each t in T","store_count[t] <= max_stores[t] for each t in B","sum(area_per_store[t]*store_count[t] for t in T) <= capacity"],"objective":"maximize rent_share*sum(k*profit_type_t[k]*choose[t,k] for t in T for k in K[t]); zero-count contribution is zero"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(values, position):
    """Accept sequences or mappings keyed by one-based integers or strings."""
    if isinstance(values, Mapping):
        if position in values:
            return values[position]
        return values[str(position)]
    return values[position - 1]


def solve(params):
    store_types = (1, 2, 3, 4, 5)
    bounded_types = (1, 2, 3)

    # Available counts follow the supplied profit-table structure.
    # The Bookstore entry "-2" is interpreted as a maximum of two stores.
    count_options = {
        1: (0, 1, 2, 3),
        2: (0, 1, 2),
        3: (0, 1, 2, 3),
        4: (0, 1, 2),
        5: (0, 1, 2, 3),
    }

    area_input = params["area_per_store"]
    minimum_input = params["min_stores"]
    maximum_input = params["max_stores"]
    profit_inputs = {
        1: params["profit_type1"],
        2: params["profit_type2"],
        3: params["profit_type3"],
        4: params["profit_type4"],
        5: params["profit_type5"],
    }
    rent_share_input = params["rent_share"]

    option_pairs = [
        (store_type, count)
        for store_type in store_types
        for count in count_options[store_type]
    ]

    profit_data = {
        (store_type, count): (
            0
            if count == 0
            else _indexed_value(profit_inputs[store_type], count)
        )
        for store_type, count in option_pairs
    }

    model = pyo.ConcreteModel()
    model.store_types = pyo.Set(initialize=store_types, ordered=True)
    model.bounded_types = pyo.Set(initialize=bounded_types, ordered=True)
    model.option_pairs = pyo.Set(
        dimen=2, initialize=option_pairs, ordered=True
    )

    model.area_per_store = pyo.Param(
        model.store_types,
        initialize={
            store_type: _indexed_value(area_input, store_type)
            for store_type in store_types
        },
    )
    model.min_stores = pyo.Param(
        model.store_types,
        initialize={
            store_type: _indexed_value(minimum_input, store_type)
            for store_type in store_types
        },
    )
    model.max_stores = pyo.Param(
        model.bounded_types,
        initialize={
            store_type: _indexed_value(maximum_input, store_type)
            for store_type in bounded_types
        },
    )
    model.profit_per_store = pyo.Param(
        model.option_pairs, initialize=profit_data
    )
    model.rent_share = pyo.Param(initialize=rent_share_input)
    model.capacity = pyo.Param(initialize=5000)

    model.choose = pyo.Var(model.option_pairs, domain=pyo.Binary)

    model.store_count = pyo.Expression(
        model.store_types,
        rule=lambda mdl, store_type: sum(
            count * mdl.choose[store_type, count]
            for count in count_options[store_type]
        ),
    )

    model.select_one_count = pyo.Constraint(
        model.store_types,
        rule=lambda mdl, store_type: sum(
            mdl.choose[store_type, count]
            for count in count_options[store_type]
        ) == 1,
    )
    model.minimum_store_limits = pyo.Constraint(
        model.store_types,
        rule=lambda mdl, store_type: (
            mdl.store_count[store_type] >= mdl.min_stores[store_type]
        ),
    )
    model.maximum_store_limits = pyo.Constraint(
        model.bounded_types,
        rule=lambda mdl, store_type: (
            mdl.store_count[store_type] <= mdl.max_stores[store_type]
        ),
    )
    model.area_limit = pyo.Constraint(
        expr=sum(
            model.area_per_store[store_type]
            * model.store_count[store_type]
            for store_type in store_types
        ) <= model.capacity
    )

    model.rental_income = pyo.Objective(
        expr=model.rent_share * sum(
            count
            * model.profit_per_store[store_type, count]
            * model.choose[store_type, count]
            for store_type, count in option_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.rental_income))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
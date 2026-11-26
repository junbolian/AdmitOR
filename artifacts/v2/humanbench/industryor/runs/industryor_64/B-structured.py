# IR: {"sets":{"G":["A","B","C","D","E"],"K":"range(U)"},"params":{"d[g]":"params['demand_'+g]","w[g]":"params['weight_'+g]","dims[g]":"params['dims_'+g]","v[g]":"product(dims[g])","Wmax":"params['container_max_weight']","Wmin":"params['container_min_weight']","L":"params['container_length']","B":"params['container_width']","H":"params['container_height']","V":"L*B*H","r":"params['coupling_AC']","q":"params['min_D_per_container']","U":"max(1,min(sum(d),floor(d['D']/ceil(q)))) if q>0 else max(1,sum(d))"},"variables":{"x[g,k]":"nonnegative integer units","y[k]":"binary container usage"},"constraints":["sum_k x[g,k] = d[g] for each g","x[g,k] <= d[g]*y[k] for each g,k","sum_g x[g,k] >= y[k] for each k","sum_g w[g]*x[g,k] <= Wmax*y[k] for each k","sum_g w[g]*x[g,k] >= Wmin*y[k] for each k","sum_g v[g]*x[g,k] <= V*y[k] for each k","x['C',k] >= r*x['A',k] for each k","x['D',k] >= q*y[k] for each k","y[k] >= y[k+1] for consecutive k"],"objective":"minimize sum_k y[k]","assumption":"Space is modeled by aggregate volume; explicit three-dimensional placement and non-overlap are not imposed."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    goods = ("A", "B", "C", "D", "E")

    demands_raw = {
        "A": params["demand_A"],
        "B": params["demand_B"],
        "C": params["demand_C"],
        "D": params["demand_D"],
        "E": params["demand_E"],
    }
    weights = {
        "A": float(params["weight_A"]),
        "B": float(params["weight_B"]),
        "C": float(params["weight_C"]),
        "D": float(params["weight_D"]),
        "E": float(params["weight_E"]),
    }
    dimensions = {
        "A": params["dims_A"],
        "B": params["dims_B"],
        "C": params["dims_C"],
        "D": params["dims_D"],
        "E": params["dims_E"],
    }

    maximum_weight = float(params["container_max_weight"])
    minimum_weight = float(params["container_min_weight"])
    container_length = float(params["container_length"])
    container_width = float(params["container_width"])
    container_height = float(params["container_height"])
    coupling_ratio = float(params["coupling_AC"])
    minimum_d = float(params["min_D_per_container"])

    demands = {}
    for good in goods:
        value = float(demands_raw[good])
        if not math.isfinite(value) or value < 0 or not value.is_integer():
            return {"objective": None, "status": "invalid_demand"}
        demands[good] = int(value)

    nonnegative_values = (
        maximum_weight,
        minimum_weight,
        coupling_ratio,
        minimum_d,
        *weights.values(),
    )
    if any(
        not math.isfinite(value) or value < 0
        for value in nonnegative_values
    ):
        return {"objective": None, "status": "invalid_parameter"}

    container_dimensions = (
        container_length,
        container_width,
        container_height,
    )
    if any(
        not math.isfinite(value) or value <= 0
        for value in container_dimensions
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    volumes = {}
    for good in goods:
        if len(dimensions[good]) != 3:
            return {"objective": None, "status": "invalid_dimensions"}
        item_dimensions = tuple(float(value) for value in dimensions[good])
        if any(
            not math.isfinite(value) or value <= 0
            for value in item_dimensions
        ):
            return {"objective": None, "status": "invalid_dimensions"}
        volumes[good] = math.prod(item_dimensions)

    total_units = sum(demands.values())
    if minimum_d > 0:
        upper_bound = max(
            1,
            min(total_units, demands["D"] // math.ceil(minimum_d)),
        )
    else:
        upper_bound = max(1, total_units)

    model = pyo.ConcreteModel()
    model.G = pyo.Set(initialize=goods, ordered=True)
    model.K = pyo.Set(initialize=range(upper_bound), ordered=True)
    model.adjacent_K = pyo.Set(initialize=range(upper_bound - 1))

    model.demand = pyo.Param(
        model.G, initialize=demands, within=pyo.NonNegativeIntegers
    )
    model.unit_weight = pyo.Param(
        model.G, initialize=weights, within=pyo.NonNegativeReals
    )
    model.unit_volume = pyo.Param(
        model.G, initialize=volumes, within=pyo.PositiveReals
    )
    model.weight_limit = pyo.Param(initialize=maximum_weight)
    model.weight_floor = pyo.Param(initialize=minimum_weight)
    model.volume_limit = pyo.Param(
        initialize=container_length * container_width * container_height
    )
    model.ac_ratio = pyo.Param(initialize=coupling_ratio)
    model.d_floor = pyo.Param(initialize=minimum_d)

    model.x = pyo.Var(model.G, model.K, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(model.K, domain=pyo.Binary)

    def demand_rule(mdl, good):
        return sum(mdl.x[good, slot] for slot in mdl.K) == mdl.demand[good]

    model.demand_balance = pyo.Constraint(model.G, rule=demand_rule)

    def usage_rule(mdl, good, slot):
        return mdl.x[good, slot] <= mdl.demand[good] * mdl.y[slot]

    model.usage_link = pyo.Constraint(model.G, model.K, rule=usage_rule)

    def nonempty_rule(mdl, slot):
        return sum(mdl.x[good, slot] for good in mdl.G) >= mdl.y[slot]

    model.nonempty_load = pyo.Constraint(model.K, rule=nonempty_rule)

    def maximum_weight_rule(mdl, slot):
        return (
            sum(mdl.unit_weight[good] * mdl.x[good, slot] for good in mdl.G)
            <= mdl.weight_limit * mdl.y[slot]
        )

    model.maximum_load_weight = pyo.Constraint(
        model.K, rule=maximum_weight_rule
    )

    def minimum_weight_rule(mdl, slot):
        return (
            sum(mdl.unit_weight[good] * mdl.x[good, slot] for good in mdl.G)
            >= mdl.weight_floor * mdl.y[slot]
        )

    model.minimum_load_weight = pyo.Constraint(
        model.K, rule=minimum_weight_rule
    )

    def volume_rule(mdl, slot):
        return (
            sum(mdl.unit_volume[good] * mdl.x[good, slot] for good in mdl.G)
            <= mdl.volume_limit * mdl.y[slot]
        )

    model.volume_capacity = pyo.Constraint(model.K, rule=volume_rule)

    def coupling_rule(mdl, slot):
        return mdl.x["C", slot] >= mdl.ac_ratio * mdl.x["A", slot]

    model.packaging_coupling = pyo.Constraint(model.K, rule=coupling_rule)

    def minimum_d_rule(mdl, slot):
        return mdl.x["D", slot] >= mdl.d_floor * mdl.y[slot]

    model.minimum_d_load = pyo.Constraint(model.K, rule=minimum_d_rule)

    def ordered_usage_rule(mdl, slot):
        return mdl.y[slot] >= mdl.y[slot + 1]

    model.ordered_usage = pyo.Constraint(
        model.adjacent_K, rule=ordered_usage_rule
    )

    model.total_containers = pyo.Objective(
        expr=sum(model.y[slot] for slot in model.K),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_containers))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
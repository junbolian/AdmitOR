import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants: products, months, product attributes, precedence
    products = [1, 2, 3, 4, 5]
    months = [1, 2, 3, 4, 5, 6]

    D = {1: 600, 2: 400, 3: 500, 4: 300, 5: 200}
    S = {1: 2000, 2: 1500, 3: 1200, 4: 1000, 5: 800}
    C = {1: 12, 2: 10, 3: 8, 4: 6, 5: 4}
    a = {1: 8, 2: 6, 3: 4, 4: 3, 5: 2}

    normal_hours = params["normal_hours"]
    max_overtime_hours = params["max_overtime_hours"]
    overtime_cost_premium = params["overtime_cost_premium"]
    penalty_p3 = params["penalty_p3"]
    penalty_p4 = params["penalty_p4"]

    if isinstance(normal_hours, dict):
        N = {k: normal_hours[k] for k in months}
    else:
        N = {k: normal_hours[k - 1] for k in months}

    if isinstance(max_overtime_hours, dict):
        O = {k: max_overtime_hours[k] for k in months}
    else:
        O = {k: max_overtime_hours[k - 1] for k in months}

    if isinstance(overtime_cost_premium, dict):
        Cp = {i: overtime_cost_premium[i] for i in products}
    else:
        Cp = {i: overtime_cost_premium[k] for k, i in enumerate(products)}

    # Earliest production month per product
    earliest = {1: 3, 2: 1, 3: 1, 4: 2, 5: 1}
    latest = {1: 6, 2: 6, 3: 6, 4: 6, 5: 6}

    # Allowed (month <= deadline) windows; deadline handled via cumulative constraints
    allowed = {}
    for i in products:
        allowed[i] = [k for k in months if earliest[i] <= k <= latest[i]]

    model = pyo.ConcreteModel()

    keys = [(i, k) for i in products for k in allowed[i]]

    model.normal = pyo.Var(keys, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(keys, domain=pyo.NonNegativeReals)

    # Delay (in months) beyond contractual deadlines for products 3 and 4
    model.delay3 = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, 2))
    model.delay4 = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, 1))

    # Total production equals contract quantity
    def _contract_rule(mdl, i):
        total = 0
        for k in allowed[i]:
            total += mdl.normal[(i, k)] + mdl.overtime[(i, k)]
        return total == D[i]

    model.contract = pyo.Constraint(products, rule=_contract_rule)

    # Product 3 cumulative production by month (4 + delay3) equals D3
    # Big-M linearization: cumulative by month t >= D3 - M*(1 - z_t) style
    # Simpler: enforce that cumulative by end of deadline+delay equals D3
    # using per-month indicator via linear expressions.
    def _p3_cum(mdl, t):
        total = 0
        for k in allowed[3]:
            if k <= t:
                total += mdl.normal[(3, k)] + mdl.overtime[(3, k)]
        return total

    BIG = D[3] + D[4] + 1e6

    # deadline for p3: month m = 4 + delay3, so require cum(4+delay3) == D3
    # Linearize: for each possible deadline value in {4,5,6}, use binary
    model.z3 = pyo.Var([4, 5, 6], domain=pyo.Binary)
    model.sum_z3 = pyo.Constraint(expr=sum(model.z3[t] for t in [4, 5, 6]) == 1)
    model.link_d3 = pyo.Constraint(
        expr=model.delay3 == sum((t - 4) * model.z3[t] for t in [4, 5, 6])
    )

    def _p3_deadline_rule(mdl, t):
        cum = _p3_cum(mdl, t)
        return cum >= D[3] - BIG * (1 - mdl.z3[t])

    model.p3_deadline = pyo.Constraint([4, 5, 6], rule=_p3_deadline_rule)

    def _p4_cum(mdl, t):
        total = 0
        for k in allowed[4]:
            if k <= t:
                total += mdl.normal[(4, k)] + mdl.overtime[(4, k)]
        return total

    model.z4 = pyo.Var([5, 6], domain=pyo.Binary)
    model.sum_z4 = pyo.Constraint(expr=sum(model.z4[t] for t in [5, 6]) == 1)
    model.link_d4 = pyo.Constraint(
        expr=model.delay4 == sum((t - 5) * model.z4[t] for t in [5, 6])
    )

    def _p4_deadline_rule(mdl, t):
        cum = _p4_cum(mdl, t)
        return cum >= D[4] - BIG * (1 - mdl.z4[t])

    model.p4_deadline = pyo.Constraint([5, 6], rule=_p4_deadline_rule)

    # Monthly capacities
    def _normal_cap_rule(mdl, k):
        hrs = 0
        for i in products:
            if k in allowed[i]:
                hrs += a[i] * mdl.normal[(i, k)]
        return hrs <= N[k]

    model.normal_cap = pyo.Constraint(months, rule=_normal_cap_rule)

    def _overtime_cap_rule(mdl, k):
        hrs = 0
        for i in products:
            if k in allowed[i]:
                hrs += a[i] * mdl.overtime[(i, k)]
        return hrs <= O[k]

    model.overtime_cap = pyo.Constraint(months, rule=_overtime_cap_rule)

    def _obj_rule(mdl):
        revenue = 0
        normal_cost = 0
        overtime_cost = 0
        for i in products:
            for k in allowed[i]:
                revenue += S[i] * (mdl.normal[(i, k)] + mdl.overtime[(i, k)])
                normal_cost += C[i] * mdl.normal[(i, k)]
                overtime_cost += (C[i] + Cp[i]) * mdl.overtime[(i, k)]
        penalty = penalty_p3 * mdl.delay3 + penalty_p4 * mdl.delay4
        return revenue - normal_cost - overtime_cost - penalty

    model.profit = pyo.Objective(rule=_obj_rule, sense=pyo.maximize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}
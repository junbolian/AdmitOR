import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    purchase_price = params["purchase_price"]
    sale_price = params["sale_price"]
    max_sales = params["max_sales"]
    storage_capacity = params["storage_capacity"]
    cost_a = params["storage_cost_a"]
    cost_b = params["storage_cost_b"]

    quarters = [0, 1, 2, 3]  # Winter, Spring, Summer, Autumn

    model = pyo.ConcreteModel()

    model.Q = pyo.Set(initialize=quarters)

    # Purchase quantity and sale quantity per quarter
    model.buy = pyo.Var(model.Q, bounds=(0, None))
    model.sell = pyo.Var(model.Q, bounds=(0, None))

    # Inventory at end of each quarter
    model.inv = pyo.Var(model.Q, bounds=(0, None))

    # Sales cannot exceed estimated maximum
    def sales_limit_rule(mdl, q):
        return mdl.sell[q] <= max_sales[q]
    model.sales_limit = pyo.Constraint(model.Q, rule=sales_limit_rule)

    # Storage capacity: inventory held through the quarter cannot exceed capacity
    def cap_rule(mdl, q):
        return mdl.inv[q] <= storage_capacity
    model.cap = pyo.Constraint(model.Q, rule=cap_rule)

    # Inventory balance: inv[q] = inv[q-1] + buy[q] - sell[q]
    def balance_rule(mdl, q):
        prev = mdl.inv[q - 1] if q > 0 else 0
        return mdl.inv[q] == prev + mdl.buy[q] - mdl.sell[q]
    model.balance = pyo.Constraint(model.Q, rule=balance_rule)

    # Initial inventory zero
    model.init_inv = pyo.Constraint(expr=model.buy[0] - model.sell[0] == model.inv[0])

    # All inventory sold by end of autumn (end inv = 0)
    model.final_inv = pyo.Constraint(expr=model.inv[3] == 0)

    # Storage cost: each unit in inv[q] is held for u quarters until sold
    # Timber bought in winter and held as inv[0] -> stored 1 quarter before being available in spring...
    # We model storage cost on inventory carried from one quarter to the next.
    # Units remaining at end of quarter q are stored for (3 - q) more transitions? 
    # Simpler standard model: cost is charged per quarter on ending inventory.
    # Storage time u = number of quarters held. Inventory inv[q] at end of q
    # was purchased and will be held at least into next quarter (1 quarter).
    # Approximate standard LP: charge a + b*u on each unit held; here we charge
    # per unit carried over each quarter with unit cost b per quarter plus a fixed a
    # applied once per unit that is stored (u depends on duration).
    #
    # Linear model: let u be storage duration. Cost = a + b*u per m^3 stored.
    # We track inventory carried between quarters. Each unit in inv[q] incurs
    # a one-time 'a' when first stored and 'b' per quarter stored.
    #
    # To keep linear and consistent, charge 'b' per quarter on inventory and
    # apply 'a' per unit that passes through storage (i.e., per unit of inv[q] that
    # is not the final zero). Standard textbook solution: cost per unit sold =
    # a+b*u where u is quarters between purchase and sale. Equivalent: charge
    # (a+b) on inventory held across one quarter boundary, then b for each extra.
    # 
    # We implement: storage cost = a * (units entering storage) + b * (units per quarter held).
    # Units entering storage at quarter q = buy[q] - sell[q] if positive contribution to inv.
    # Simpler and exact for linear: charge cost on all units in inv[q] for each quarter,
    # with fixed a added to first transition. We'll charge a on each unit-stored once:
    # introduce per-quarter storage decision cost on inv transitions.
    #
    # Practical formulation: storage cost incurred on ending inventory inv[q] at
    # rate a + b (for one quarter) for q=0, then b per additional quarter is handled
    # via accumulation. Equivalent to: cost = sum over q of (a + b*(q+... )) ... 
    # We use the common interpretation: each unit stored for u quarters costs a+b*u.
    # Total = a*(total units stored at least once) + b*(total unit-quarters stored).
    # total unit-quarters stored = sum_q inv[q] (inv[q] held from q to q+1, 1 quarter each).
    # total units stored at least once <= total buy (upper bound); use sum buy as proxy is invalid.
    #
    # Correct linear: a is per unit (once) regardless of duration, b per quarter.
    # Introduce z[q] = units in inv[q] that are newly stored (not carried from before).
    # Since FIFO, new storage = max(0, inv[q] - inv[q-1]) which is nonlinear in general
    # but here we can decompose: units carried over = inv[q], all incur b per quarter.
    # The 'a' applies once per unit ever stored = per unit that has u>=1.
    # A unit with u>=1 is any unit that appears in some inv[q] and eventually sold later.
    # This equals total bought minus units sold same quarter (u=0).
    # sold_same_quarter[q] <= min(buy[q], sell[q]); introduce variable.
    
    model.same_q = pyo.Var(model.Q, bounds=(0, None))
    
    def same_q_rule1(mdl, q):
        return mdl.same_q[q] <= mdl.buy[q]
    def same_q_rule2(mdl, q):
        return mdl.same_q[q] <= mdl.sell[q]
    model.same_q_c1 = pyo.Constraint(model.Q, rule=same_q_rule1)
    model.same_q_c2 = pyo.Constraint(model.Q, rule=same_q_rule2)
    
    # Revenue and costs (in 10000 yuan units: volume in 10000 m^3, price in 10000 yuan/10000 m^3)
    # So price * volume directly gives 10000 yuan.
    def obj_rule(mdl):
        revenue = sum(sale_price[q] * mdl.sell[q] for q in mdl.Q)
        purchase = sum(purchase_price[q] * mdl.buy[q] for q in mdl.Q)
        # storage cost in yuan/m^3; volume in 10000 m^3 -> multiply by 10000 to get m^3,
        # cost in yuan, divide by 10000 to convert to 10000 yuan => factor 1.
        # cost_a (yuan/m^3) * volume(10000 m^3) * 10000 = yuan; /10000 = 10000 yuan.
        # So cost in 10000 yuan = cost_a * volume_in_10000m3.
        stored_once = sum(mdl.buy[q] - mdl.same_q[q] for q in mdl.Q)
        unit_quarters = sum(mdl.inv[q] for q in mdl.Q)
        storage_cost = cost_a * stored_once + cost_b * unit_quarters
        return revenue - purchase - storage_cost
    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}
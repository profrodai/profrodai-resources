export interface Order {
  id: string;
  customerId: string;
  total: number;
  status: "pending" | "shipped" | "delivered";
}

const orders = new Map<string, Order>([
  ["ord_1", { id: "ord_1", customerId: "cus_1", total: 42.5, status: "shipped" }],
  ["ord_2", { id: "ord_2", customerId: "cus_1", total: 18.0, status: "pending" }],
  ["ord_4", { id: "ord_4", customerId: "cus_1", total: 64.0, status: "delivered" }],
  ["ord_5", { id: "ord_5", customerId: "cus_1", total: 27.5, status: "pending" }],
  ["ord_3", { id: "ord_3", customerId: "cus_2", total: 91.2, status: "delivered" }],
]);

export function getOrder(id: string): Order {
  const order = orders.get(id);
  if (!order) throw new Error(`Order not found: ${id}`);
  return order;
}

export function listOrders(customerId: string): Order[] {
  return [...orders.values()].filter((o) => o.customerId === customerId);
}

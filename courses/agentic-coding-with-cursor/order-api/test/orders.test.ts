import { OrderClient } from "../src/client";
import { getOrder, listOrders } from "../src/orders";

test("getOrder returns a known order", () => {
  expect(getOrder("ord_1").status).toBe("shipped");
});

test("getOrder throws for an unknown id", () => {
  expect(() => getOrder("nope")).toThrow();
});

test("listOrders filters by customer", () => {
  expect(listOrders("cus_1")).toHaveLength(4);
});

test("listOrders returns an empty array for an unknown customer", () => {
  expect(listOrders("cus_nobody")).toEqual([]);
});

test("cached customer views keep every output-affecting option in the key", () => {
  const client = new OrderClient();

  const firstPending = client.listForCustomer("cus_1", { status: "pending", limit: 1 });
  const allOrders = client.listForCustomer("cus_1");
  const delivered = client.listForCustomer("cus_1", { status: "delivered" });

  expect(firstPending).toHaveLength(1);
  expect(allOrders).toHaveLength(4);
  expect(delivered.map((order) => order.id)).toEqual(["ord_4"]);
});

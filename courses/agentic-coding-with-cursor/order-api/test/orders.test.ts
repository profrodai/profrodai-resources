import { getOrder, listOrders } from "../src/orders";

test("getOrder returns a known order", () => {
  expect(getOrder("ord_1").status).toBe("shipped");
});

test("getOrder throws for an unknown id", () => {
  expect(() => getOrder("nope")).toThrow();
});

test("listOrders filters by customer", () => {
  expect(listOrders("cus_1")).toHaveLength(2);
});

test("listOrders returns an empty array for an unknown customer", () => {
  expect(listOrders("cus_nobody")).toEqual([]);
});

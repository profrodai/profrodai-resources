import { getOrder, listOrders } from "./orders";

export class OrderClient {
  get(id: string) {
    return getOrder(id);
  }

  listForCustomer(customerId: string) {
    return listOrders(customerId);
  }
}

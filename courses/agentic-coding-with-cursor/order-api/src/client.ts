import { getOrder, listOrders, type Order } from "./orders";

export interface ListOptions {
  limit?: number;
  status?: Order["status"];
}

type CachedOrders = {
  orders: Order[];
  cachedAt: number;
};

const CACHE_TTL_MS = 60_000;

export class OrderClient {
  private readonly listCache = new Map<string, CachedOrders>();

  get(id: string) {
    return getOrder(id);
  }

  listForCustomer(customerId: string, options: ListOptions = {}) {
    const cacheKey = JSON.stringify({
      customerId,
      limit: options.limit ?? null,
      status: options.status ?? null,
    });
    const cached = this.listCache.get(cacheKey);
    if (cached && Date.now() - cached.cachedAt < CACHE_TTL_MS) {
      return [...cached.orders];
    }

    const filtered = listOrders(customerId).filter(
      (order) => !options.status || order.status === options.status,
    );
    const orders = options.limit === undefined ? filtered : filtered.slice(0, options.limit);
    this.listCache.set(cacheKey, { orders: [...orders], cachedAt: Date.now() });
    return orders;
  }
}

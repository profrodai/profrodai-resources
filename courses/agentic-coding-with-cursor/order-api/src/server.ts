import express from "express";
import { OrderClient } from "./client";

const app = express();
app.use(express.json());
const client = new OrderClient();

app.get("/orders/:id", (req, res) => {
  res.json(client.get(req.params.id));
});

app.get("/customers/:id/orders", (req, res) => {
  res.json(client.listForCustomer(req.params.id));
});

app.post("/orders", (req, res) => {
  res.status(201).json({ received: true });
});

// Keep importing the app side-effect free so the deterministic test suite can
// exercise it without binding a local port.
if (require.main === module) {
  const port = process.env.PORT ? Number(process.env.PORT) : 3000;
  app.listen(port, () => {
    console.log(`order-api listening on http://localhost:${port}`);
  });
}

export default app;
